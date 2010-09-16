"""
masterserver.py

Runs a Master Server query for Valve games using the protocol specified in:
http://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol

It then adds the results to the database.  This script is designed to be run as a cron job
"""

from paste.deploy import appconfig
from pylons import config
import socket

from gamelion.config.environment import load_environment

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

from gamelion.model import *
import gamelion.lib.stringz as struct
import struct as pystruct

master_servers = [ ('hl2master.steampowered.com', 27011) ]

_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.settimeout(2.0)

def pack_query(region, ip_port, filter):
    """ Pack a Master Server Query """
    return struct.pack('!2Bzz', 0x31, region, ip_port, filter)

def query_server(address, data):
    """
    Send a single query packet to the master server at address, the full query is made up
    of a group of these
    """
    _socket.sendto(data, address)

def receive_response():
    """ Block and receive a response from the master server (with a timeout) """

    response = ''
    try:
        response = _socket.recv(2048)
    except socket.timeout:
        response = ''

    return response

def unpack_response(response):
    """ Unpack a response from a master server, and return the results in a list """
    if len(response) == 0:
        return []

    ips = []
    entry_format = '!4sH'
    header_format = '6s'
    entry_size = pystruct.calcsize(entry_format)
    header_size = pystruct.calcsize(header_format)
    offset = 0

    # Strip off the header
    header = struct.unpack('6s', response)
    response = response[header_size:]

    # Get our (ip, port) pairs and put them in a pretty format
    while len(response) >= entry_size:
        (ip, port) = struct.unpack(entry_format, response)
        response = response[entry_size:]

        ip_string = socket.inet_ntoa(ip)
        ips.append((ip_string, port))

    return ips

def run_full_query(server_address):
    """ Run a full master server query """

    servers = [('0.0.0.0', 0)]

    # get all the ips the master server wishes to give us
    while len(servers) <= 1 or servers[-1] != ('0.0.0.0', 0):

        # get a string for the last ip the server sent us
        previous_server = '%s:%d' % (servers[-1])

        # Prepare our query with region, last ip, and filter
        query_data = pack_query(0x01, previous_server, r'\napp\500\proxy\1')

        # Tell the server we'd like some data
        query_server(server_address, query_data)

        # Wait to hear back, and add the results to the list
        response = receive_response()
        servers.extend(unpack_response(response))

    assert servers[0] == ('0.0.0.0', 0)
    assert servers[-1] == ('0.0.0.0', 0)
    servers = servers[1:-1]

    return servers

def add_results_to_database(server_list):
    """ Add a list of ips and ports to the database """
    for ip, port in server_list:
        exists_query = Session.query(Server).filter(Server.address == ip).filter(Server.port == port).first()
        if not exists_query:
            server = Server()
            server.address = ip
            server.port = port
            Session.add(server)
            Session.commit()

def main():
    """ Query the master server and add the results to the database """
    servers = []

    # run through all the master servers we know of and ask them for ips
    for server_address in master_servers:
        servers.extend(run_full_query(server_address))

    # add everything we got to the database
    add_results_to_database(servers)

if __name__ == '__main__':
    main()
