import time
import socket
import select
import struct as pystruct

from paste.deploy import appconfig
from pylons import config

import gamelion.lib.stringz as struct
from gamelion.config.environment import load_environment
from gamelion.model import *
import logging
from optparse import OptionParser
import gamelion.lib.queryserver as QueryServer
from sqlalchemy.sql.expression import func
from amqplib import client_0_8 as amqp

# set up the pylons environment
conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# define a query
class GameServerQuery(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.times_sent = 0

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
        #logging.debug('querying: %s %d', self.server.address, self.server.port)
        sock.sendto(data, (self.address, self.port))
        self.times_sent += 1

    def process_response(self, response):
        # get the message header to see if it's a split message or not
        # TODO: handle split responses
       
        try:
            info_response = QueryServer.InfoResponse(response)
        except Exception as e:
            logging.debug(str(e))
            return False
            
        
        #if self.server.name == None:
        #    logging.debug('ADDING SERVER: %s', info_response.name)
        #else:
        
        logging.debug('UPDATING SERVER: %s', info_response.name)
        
        # if this app id doesn't exist, add it and use the game name
        # supplied in the response
        if Session.query(Game)\
                  .filter(Game.id == info_response.app_id)\
                  .first() == None:
            logging.debug('ADDING APP ID: %d, %s', 
                          info_response.app_id,
                          info_response.description)
            game = Game()
            game.id = info_response.app_id
            game.name = unicode(info_response.description, encoding='latin_1')
            Session.add(game)
            Session.commit()

        server = Server()
        server.address = self.address
        server.port = self.port

        # fill in the rest of the response data
        info_response.fill_server(server)
        server = Session.merge(server)
        Session.add(server)

        return True

query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_queue = {}
MAX_QUEUE_SIZE = 10

def process_server_queue():
    global server_queue
    TIMEOUT = 3
    MAX_ATTEMPTS = 5

    while len(server_queue) > 0:
        queries_to_send = server_queue.values()

        for query in queries_to_send[:5]: # only send a few at a time
            if query.times_sent > MAX_ATTEMPTS:
                logging.debug(
                    'GIVING UP ON %s:%d, TIMED OUT %d TIMES', 
                    query.address, 
                    query.port, 
                    MAX_ATTEMPTS
                )
               
                del server_queue[(query.address, query.port)]
            else:
                query.send(query_socket)

        # process response(s) if we got any (i.e. didn't time out)
        while True:
            readable, _, _ = select.select([query_socket], [], [], TIMEOUT)

            if len(readable) == 0:
                break

            data, source = query_socket.recvfrom(2048)
            addr, port = source

            if source in server_queue:
                query_complete = server_queue[source].process_response(data)
                if query_complete:
                    del server_queue[source]
                break
    
    # commit completed queries
    Session.commit()

def receive_message(message):
    headers = message.properties['application_headers']
    ip = headers['ip']
    port = headers['port']
    server_queue[(ip, port)] = GameServerQuery(ip, port)

    if len(server_queue) >= MAX_QUEUE_SIZE:
        process_server_queue()

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    connection = amqp.Connection(
        host='localhost:5672',
        userid='alex',
        password='alex',
        virtual_hose='/',
        insist=False
    )

    channel = connection.channel()
    channel.queue_declare(
        queue='servers', 
        durable=True, 
        exclusive=False, 
        auto_delete=False
    )

    channel.queue_bind(
        queue='servers',
        exchange='gamelion_servers',
        routing_key='gamelion'
    )

    channel.basic_consume(
        queue='servers',
        no_ack=True,
        callback=receive_message,
        consumer_tag='gameserver'
    )

    while True:
        channel.wait()
        
    channel.basic_cancel('gameserver')
    channel.close()
    connection.close()
