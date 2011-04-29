import time
from datetime import datetime
from datetime import timedelta
import socket
import select
import struct as pystruct

from paste.deploy import appconfig
from pylons import config
from gamelion.config.environment import load_environment
from gamelion.model import *

import gamelion.lib.stringz as struct
import logging
from optparse import OptionParser
import gamelion.lib.queryserver as QueryServer
from kombu.connection import BrokerConnection
from kombu.messaging import Queue, Exchange, Consumer
import sqlalchemy

# set up the pylons environment
conf = appconfig('config:amazon.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# globals
query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_buffer = {}
display_waiting = True
last_waiting_time = datetime.now() 

QUERY_CHUNK_SIZE = 25 
CONSUME_TIMEOUT = 5
MAX_SERVER_LIFETIME_TIMEOUTS = 10

# define a query
class GameServerQuery(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.times_sent = 0

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
        
        try:
            sock.sendto(data, (self.address, self.port))
        except socket.error as e:
            logging.debug(str(e))

        self.times_sent += 1

    def process_response(self, response):
        # get the message header to see if it's a split message or not
        # TODO: handle split responses
       
        try:
            info_response = QueryServer.InfoResponse(response)
        except Exception as e:
            return False
        
        # if this app id doesn't exist, add it and use the game name
        # supplied in the response
        before_time = time.time()
        try:
            if not Session.query(Game).get(info_response.app_id):
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

            after_time = time.time()
            if (after_time - before_time) > 1.0:
                logging.debug(
                    'GAME QUERY TOOK: %f', 
                    after_time - before_time
                )

            server = Server()
            server.address = self.address
            server.port = self.port

            # fill in the rest of the response data
            info_response.fill_server(server)
            server = Session.merge(server)
            Session.add(server)

        except sqlalchemy.exc.IntegrityError:
            logging.debug(
                'GOT INTEGRITY ERROR, SERVER ALREADY ' + 
                'INSERTED BY ANOTHER PROCESS' 
            )
            Session.rollback()
            return False

        return True

    def increment_timeouts(self):
        server = Session.query(Server).get((self.address, self.port))
        if server:
            if server.timeouts >= MAX_SERVER_LIFETIME_TIMEOUTS:
                logging.debug(
                    'DELETING SERVER, EXCEEDED LIFETIME TIMEOUTS: %s', 
                    server.name
                )
                Session.delete(server)
            else:
                server.timeouts += 1
                Session.add(server)

def process_servers():
    TIMEOUT = 2 
    MAX_ATTEMPTS = 3 
    global server_buffer

    before = len(server_buffer)
    before_time = time.time()
    timeouts = before

    queries_to_send = server_buffer.values()
    while len(queries_to_send) > 0:
        # send some queries
        for query in queries_to_send[:QUERY_CHUNK_SIZE]:
            query.send(query_socket)

        # we've sent these queries. prepare the next ones
        queries_to_send = queries_to_send[QUERY_CHUNK_SIZE:]

        # process response(s) if we got any (i.e. didn't time out)
        while True:
            readable, _, _ = select.select([query_socket], [], [], TIMEOUT)

            if len(readable) == 0:
                break

            data, source = query_socket.recvfrom(2048)

            if source in server_buffer:
                query_object = server_buffer[source]
                query_complete = query_object.process_response(data)
                if query_complete:
                    timeouts -= 1
                    del server_buffer[source]
   
    assert len(server_buffer) == timeouts

    # increment timeout counter on timed out servers
    for timed_out_server in server_buffer.values():
        timed_out_server.increment_timeouts()

    # clear out timed out servers
    server_buffer.clear()

    # commit completed queries
    Session.commit()

    after_time = time.time()
    logging.debug(
        'QUERIED %d SERVERS (%d TIME OUTS), TOOK %f SECONDS', 
        before,
        timeouts,
        after_time - before_time
    )

def parse_message(body):
    global server_buffer
    address_strings = body.split('|')

    # insert all the addresses in this message into 
    # the local buffer
    for address in address_strings:
        if ':' not in address:
            logging.debug('INVALID ADDRESS PARSED: %s', str(address))
            continue
        else:
            (ip, port) = address.split(':')
            port = int(port)
            server_buffer[(ip, port)] = GameServerQuery(ip, port)

def receive_message(body, message):
    global display_waiting
    global last_waiting_time

    if not display_waiting:
        display_waiting = True
        last_waiting_time = datetime.now()

    parse_message(body)
    process_servers()
    
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
                processing_time = datetime.now() -\
                                  last_waiting_time -\
                                  timedelta(seconds=CONSUME_TIMEOUT)

                logging.debug(
                    '... WAITING ... TIME SINCE LAST: %s',
                    processing_time
                )
                display_waiting = False
        
    connection.close()
