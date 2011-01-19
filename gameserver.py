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

# set up the pylons environment
conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# define a query
class GameServerQuery(object):
    def __init__(self, server):
        self.server = server
        self.time = 0
        self.times_sent = 0

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
        sock.sendto(data, (self.server.address, self.server.port))
        self.time = time.time()
        self.times_sent += 1

    def process_response(self, response):
        # get the message header to see if it's a split message or not
        # TODO: handle split responses
        header, = struct.unpack('<i', response)
        response = response[pystruct.calcsize('i'):]
        assert header == -1

        # unpack the rest of the data
        _, _, name, _, _, title, app_id = struct.unpack('<cczzzzh', response)
        self.server.name = unicode(name, encoding='latin_1')
        self.server.app_id = app_id

        # if this app id doesn't exist, add it and use the game name
        # supplied in the response
        if Session.query(Game).filter(Game.id == app_id).first() == None:
            logging.debug('adding app id: %d, %s', app_id, title)
            game = Game()
            game.id = app_id
            game.name = unicode(title, encoding='latin_1')
            Session.add(game)
            Session.commit()

        return True

# main loop
def query_servers(query_found_only):
    TIMEOUT = 3 # seconds
    MAX_ATTEMPTS = 5 # only try queries 5 times before we give up

    server_query = Session.query(Server)
    
    if query_found_only:
        # only get servers with a name already filled in
        server_query = server_query.filter(Server.name != None)
    else:
        # query un-queried servers first
        server_query = server_query.order_by(Server.name != None)
        
    servers = server_query.all()
    queries = map(lambda s: GameServerQuery(s), servers) 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while len(queries) > 0:
        # send a few outstanding queries
        queries_under_max = filter(lambda q: q.times_sent < MAX_ATTEMPTS,
                                    queries)

        if len(queries_under_max) == 0:
            logging.debug("%d queries didn't make it", len(queries))
            break

        now = time.time()
        queries_to_send = filter(lambda q: now - q.time > TIMEOUT,
                                 queries_under_max)

        for query in queries_to_send[:10]: # only send a few at a time
            query.send(sock)

        # process response(s) if we got any (i.e. didn't time out)
        while True:
            readable, _, _ = select.select([sock], [], [], 0)

            if len(readable) == 0:
                break

            data, source = sock.recvfrom(2048)
            addr, port = source

            for query in queries:
                if query.server.address == addr and\
                   query.server.port == port:
                    query_complete = query.process_response(data)
                    if query_complete:
                        logging.debug('queries left: %d', len(queries))
                        queries.remove(query)
                    break

        Session.commit()

        # sleep a little while to avoid overdoing it
        time.sleep(.1)

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

    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error('incorrect number of arguments')

    logging.basicConfig(level=logging.DEBUG)
    if not options.debug:
        logging.disable(logging.DEBUG)

    query_servers(options.query_found_only)

