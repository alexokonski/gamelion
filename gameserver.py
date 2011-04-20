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
from kombu.connection import BrokerConnection
from kombu.messaging import Queue, Exchange, Consumer

# set up the pylons environment
conf = appconfig('config:amazon.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# globals
query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_buffer = {}
display_waiting = True

QUERY_CHUNK_SIZE = 20 
MAX_BUFFER_SIZE = 100
CONSUME_TIMEOUT = 10


# define a query
class GameServerQuery(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.times_sent = 0

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
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
            game.name = unicode(
                info_response.description, 
                encoding='latin_1'
            )
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

def process_servers():
    TIMEOUT = 2 
    MAX_ATTEMPTS = 3 
    global server_buffer

    before = len(server_buffer)
    before_time = time.time()
    timeouts = 0

    while len(server_buffer) > 0:
        queries_to_send = server_buffer.values()

        for query in queries_to_send[:QUERY_CHUNK_SIZE]:
            if query.times_sent > MAX_ATTEMPTS:
                #logging.debug(
                #    'GIVING UP ON %s:%d, TIMED OUT %d TIMES', 
                #    query.address, 
                #    query.port, 
                #    MAX_ATTEMPTS
                #)
                timeouts += 1
                del server_buffer[(query.address, query.port)]
            else:
                query.send(query_socket)

        # process response(s) if we got any (i.e. didn't time out)
        while True:
            readable, _, _ = select.select([query_socket], [], [], TIMEOUT)

            if len(readable) == 0:
                break

            data, source = query_socket.recvfrom(2048)
            addr, port = source

            if source in server_buffer:
                query_object = server_buffer[source]
                query_complete = query_object.process_response(data)
                if query_complete:
                    del server_buffer[source]
    
    # commit completed queries
    Session.commit()
    after_time = time.time()
    after = len(server_buffer)
    logging.debug(
        'QUERIED %d SERVERS (%d TIME OUTS), TOOK %f SECONDS', 
        before - after,
        timeouts,
        after_time - before_time
    )


def receive_message(body, message):
    global display_waiting
    global server_buffer
    display_waiting = True

    (ip, port) = body.split(':')
    port = int(port)
    server_buffer[(ip, port)] = GameServerQuery(ip, port)

    if len(server_buffer) > MAX_BUFFER_SIZE:
        process_servers()
        after = len(server_buffer)

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.DEBUG)

    server_exchange = Exchange('servers', type='fanout')
    server_queue = Queue('servers', exchange=server_exchange)

    connection = BrokerConnection(
        hostname='localhost',
        userid='alex',
        password='alex',
        virtual_hose='/'
    )
    channel = connection.channel()
   
    consumer = Consumer(channel, server_queue)
    consumer.register_callback(receive_message)
    consumer.consume(no_ack=True)
   
    while True:
        try:
            connection.drain_events(timeout=CONSUME_TIMEOUT)
        except socket.timeout:
            # flush the server buffer if we haven't gotten
            # any messages in a while
            if len(server_buffer) > 0:
                logging.debug('QUEUE TIMED OUT, FLUSHING BUFFER')
                process_servers()
            elif display_waiting:
                logging.debug('... WAITING ...')
                display_waiting = False
        
    connection.close()
