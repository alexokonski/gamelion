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

    def send(self, sock):
        data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
        sock.sendto(data, (self.server.address, self.server.port))
        self.time = time.time()

    def process_response(self, response):
        # get the message header to see if it's a split message or not
        # TODO: handle split responses
        header, = struct.unpack('<i', response)
        response = response[pystruct.calcsize('i'):]
        assert header == -1

        # unpack the rest of the data
        server_info = struct.unpack('<cczzzzhccccccczc', response)
        self.server.name = server_info[2]
        Session.commit()
        return True

# main loop
if __name__ == "__main__":
    TIMEOUT = 3 # seconds

    servers = Session.query(Server).all()
    queries = map(lambda s: GameServerQuery(s), servers)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while len(queries) > 0:
        # send a few outstanding queries
        now = time.time()
        queries_to_send = filter(lambda q: now - q.time > TIMEOUT, queries)

        for query in queries_to_send[:5]: # only send a few at a time
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
                        queries.remove(query)
                    break

        # sleep a little while to avoid overdoing it
        time.sleep(.1)

