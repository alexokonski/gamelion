import time
import socket
import select
import struct as pystruct
from datetime import datetime

from paste.deploy import appconfig
from pylons import config

import gamelion.lib.stringz as struct
from gamelion.config.environment import load_environment
from gamelion.model import *
import logging
from optparse import OptionParser
import gamelion.lib.queryserver as QueryServer
from sqlalchemy.sql.expression import func

# set up the pylons environment
conf = appconfig('config:../amazon.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# define a query
class GameServerQuery(object):
    def __init__(self, server):
        self.server = Session.merge(server)
        self.time = 0
        self.times_sent = 0

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
        #logging.debug('querying: %s %d', self.server.address, self.server.port)
        sock.sendto(data, (self.server.address, self.server.port))
        self.time = time.time()
        self.times_sent += 1

    def process_response(self, response):
        # get the message header to see if it's a split message or not
        # TODO: handle split responses

        before = time.time()
        info_response = QueryServer.InfoResponse(response)
        print '********************* PARSING TOOK', time.time() - before

        if self.server.name == None:
            logging.debug('ADDING SERVER: %s', info_response.name)
        else:
            logging.debug('UPDATING SERVER: %s', info_response.name)
        
        Session.autoflush = False
        before = time.time()
        game = Game()
        game.id = info_response.app_id
        game.name = unicode(info_response.description, encoding='utf-8')
        
        self.server.game = Session.merge(game)
        self.server = Session.merge(self.server)
        info_response.fill_server(self.server)
        print '************** FILLING TOOK', time.time() - before
        Session.autoflush = True
        return True

# main loop
def query_servers(query_found_only, query_in_random_order, address):
    TIMEOUT = 3 # seconds
    MAX_ATTEMPTS = 5 # only try queries 5 times before we give up

    # number of complete queries required before they are committed (for speed) 
    COMPLETE_QUERIES_REQUIRED = 10

    server_query = Session.query(Server)
    
    if address != None:
        (ip, port) = address.split(':')
    else:
        if query_found_only:
            # only get servers with a name already filled in
            server_query = server_query.filter(Server.name != None)

        if query_in_random_order:
            # query servers in a random order 
            server_query = server_query.order_by(func.random())
        else:
            # query un-queried servers first
            server_query = server_query.order_by(Server.name != None)

    logging.debug('RUNNING QUERY')
    if address == None:
        servers = server_query.all()
    else:
        servers = []

    logging.debug('GOT %d SERVERS', len(servers))
    logging.debug('QUERY COMPLETE')

    logging.debug('GENERATING DICT')

    queries = {}
    if address != None and len(servers) == 0:
        server = Server()
        server.address = ip
        server.port = int(port)
        queries[(server.address, server.port)] = GameServerQuery(server)
    else:
        for server in servers:
            queries[(server.address, server.port)] = GameServerQuery(server)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    complete_queries = 0
    while len(queries) > 0:
        # send a few outstanding queries
        queries_under_max = filter(lambda q: q.times_sent < MAX_ATTEMPTS,
                                    queries.values())

        if len(queries_under_max) == 0:
            logging.debug("%d queries didn't make it", len(queries))
            break

        now = time.time()
        queries_to_send = filter(lambda q: now - q.time > TIMEOUT,
                                 queries_under_max)

        for query in queries_to_send[:5]: # only send a few at a time
            query.send(sock)

        # process response(s) if we got any (i.e. didn't time out)
        while True:
            readable, _, _ = select.select([sock], [], [], TIMEOUT)

            if len(readable) == 0:
                break

            data, source = sock.recvfrom(2048)
            addr, port = source

            if source in queries:
                logging.debug('PROCESSING QUERY FROM %s', str(source))
                query_complete = queries[source].process_response(data)
                if query_complete:
                    complete_queries += 1
                    del queries[source]
                break

        if complete_queries >= COMPLETE_QUERIES_REQUIRED:
            logging.debug('COMMITTING')
            #Session.commit()
            logging.debug('COMMIT COMPLETE')
            complete_queries = 0

        # sleep a little while to avoid overdoing it
        time.sleep(1)
    
    # commit any outstanding completed queries
    Session.commit()

if __name__ == "__main__":
    usage = 'usage: gameserver.py [options]'
    parser = OptionParser(usage)
    parser.add_option('-d', '--debug',
                      action='store_true', dest='debug', default=False,
                      help='enable debug messages')
    parser.add_option('-f', '--query-found-only',
                      action='store_true', dest='query_found_only', 
                      default=False, 
                      help='only query servers that have already responded\
                            at least once (that is, they have a name)')
    parser.add_option('-r', '--random',
                      action='store_true', dest='query_in_random_order',
                      default=False,
                      help='query servers in random order.  Can be combined with -f')

    parser.add_option('-a', '--address',
                      action='store', dest='address', type="string",
                      help='address to query, in form ip:port')

    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error('incorrect number of arguments')

    logging.basicConfig(level=logging.DEBUG)
    if not options.debug:
        logging.disable(logging.DEBUG)

    query_servers(options.query_found_only, 
                  options.query_in_random_order, 
                  options.address)

