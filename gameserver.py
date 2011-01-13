import time
import socket
import select
import struct as pystruct

from paste.deploy import appconfig
from pylons import config

import gamelion.lib.stringz as struct
from gamelion.config.environment import load_environment
from gamelion.model import *

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
        server_info = struct.unpack('<cczzzzhcccccccz', response)
        self.server.name = unicode(server_info[2], encoding='latin_1')
        return True

# main loop
if __name__ == "__main__":
    TIMEOUT = 3 # seconds
    MAX_ATTEMPTS = 5 # only try queries 5 times before we give up

    servers = Session.query(Server).all()
    queries = map(lambda s: GameServerQuery(s), servers) 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while len(queries) > 0:
        # send a few outstanding queries
        queries_under_max = filter(lambda q: q.times_sent < MAX_ATTEMPTS,
                                    queries)

        if len(queries_under_max) == 0:
            print len(queries), "queries didn't make it"
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
                if query.server.address == addr and query.server.port == port:
                    query_complete = query.process_response(data)
                    if query_complete:
                        print 'queries left:', len(queries)
                        queries.remove(query)
                    break

        Session.commit()

        # sleep a little while to avoid overdoing it
        time.sleep(.1)

