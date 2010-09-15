from paste.deploy import appconfig
from pylons import config
import socket

from gamelion.config.environment import load_environment

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

from gamelion.model import *
import gamelion.lib.stringz as struct
import struct as pystruct

class MasterServerQuery(object):
    master_servers = [ ('hl2master.steampowered.com', 27011) ]

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(2.0)

    def _pack_query(self, region, ip_port, filter):
        return struct.pack('!2Bzz', 0x31, region, ip_port, filter)

    def _query_server(self, address, data):
        print repr(data)
        self.socket.sendto(data, address)

    def _receive_response(self):
        response = ''
        try:
            response = self.socket.recv(2048)
        except socket.timeout:
            response = ''

        return response

    def _unpack_response(self, response):
        if len(response) == 0:
            return []

        ips = []
        entry_format = '!4sH'
        header_format = '6s'
        entry_size = pystruct.calcsize(entry_format)
        header_size = pystruct.calcsize(header_format)
        offset = 0

        header = struct.unpack('6s', response)
        response = response[header_size:]

        while len(response) >= entry_size:
            (ip, port) = struct.unpack(entry_format, response)
            response = response[offset:]
            offset += entry_size

            ip_string = socket.inet_ntoa(ip)
            ips.append((ip_string, port))

        print ips[-1]
        return ips

    def _run_full_query(self, server_address):
        servers = [('0.0.0.0', 0)]
        while len(servers) <= 1 or servers[-1] != ('0.0.0.0', 0):
            previous_server = '%s:%d' % (servers[-1])
            #print previous_server
            query_data = self._pack_query(0x01, previous_server, '\\napp\\500\\full\\1\\proxy\\1')
            self._query_server(server_address, query_data)
            response = self._receive_response()
            servers.extend(self._unpack_response(response))
            #print servers

        return servers

    def run(self):
        servers = []
        for server_address in MasterServerQuery.master_servers:
            servers.extend(self._run_full_query(server_address))

        print servers

if __name__ == '__main__':
    server_query = MasterServerQuery()
    server_query.run()
