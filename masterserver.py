"""
masterserver.py

Runs a Master Server query for Valve games using the protocol specified in:
http://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol

It then adds the results to the database.  This script is designed 
to be run as a cron job
"""

from paste.deploy import appconfig
from pylons import config

from gamelion.config.environment import load_environment

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

from gamelion.model import *
import gamelion.lib.stringz as struct
import struct as pystruct
import socket
import time
import logging
from optparse import OptionParser
from amqplib import client_0_8 as amqp

master_servers = [ ('hl2master.steampowered.com', 27011) ]

query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
query_socket.settimeout(1.0)

def pack_query(region, ip_port, filter):
    """ Pack a Master Server Query """
    return struct.pack('!2Bzz', 0x31, region, ip_port, filter)

def query_server(address, data):
    """
    Send a single query packet to the master server at address, 
    the full query is made up of a group of these
    """
    query_socket.sendto(data, address)

def receive_response():
    """ 
    Block and receive a response from the master server 
    (with a timeout) 
    """

    response = ''
    try:
        (response, address) = query_socket.recvfrom(2048)
    except socket.timeout:
        logging.debug('TIMEOUT')
        response = ''

    return response

def unpack_response(response):
    """ 
    Unpack a response from a master server, and 
    return the results in a list 
    """
    
    if len(response) == 0:
        return []

    ips = []
    entry_format = '!4sH'
    header_format = '!6s'
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

    assert len(response) == 0

    return ips

def run_full_query(server_address):
    """ Run a full master server query """
    
    DEFAULT_IP = ('0.0.0.0', 0)
    MAX_ITERATIONS = 10000

    servers = set()
    previous_server = DEFAULT_IP

    amqp_connection = amqp.Connection(
        host='localhost:5672', 
        userid='alex', 
        password='alex',
        virtual_host='/',
        insist=False
    )

    amqp_channel = amqp_connection.channel()

    i = 0
    # get all the ips the master server wishes to give us
    while i < MAX_ITERATIONS and (len(servers) <= 1 or
                                  previous_server != DEFAULT_IP):

        logging.debug('')
        logging.debug('-' * 60)

        # get a string for the last ip the server sent us
        server_string = '%s:%d' % (previous_server)
        query_data = pack_query(0xFF, server_string, r'\napp\500\napp\550')
        print repr(query_data)

        # Tell the server we'd like some data
        query_server(server_address, query_data)

        # Wait to hear back, and add the results to the list
        response = receive_response()
        response_servers = unpack_response(response)
        
        if len(response_servers) > 0 and\
           response_servers[-1] not in servers:
            # We just got a list that (presumably) we haven't
            # seen yet.  Grab the last one to use as the next 'seed'
            previous_server = response_servers[-1]

            # Attempt to commit all the new ips to the database
            #logging.debug('ATTEMPTING TO ADD: %d', len(response_servers))
            #add_results_to_database(response_servers)
    
            # add these servers to the queue
            for ip, port in response_servers:
                logging.debug('SENDING %s, %d', ip, port)
                message = amqp.Message()
                message.properties['application_headers'] = { 
                    'ip': ip, 
                    'port': port 
                }
                message.properties['delivery_mode'] = 1
                amqp_channel.basic_publish(
                    message, 
                    exchange='gamelion_servers', 
                    routing_key='gamelion'
                )

            # update our list of servers so we'll be able to know if 
            # we get another new list
            servers.update(response_servers)

        elif len(response_servers) == 0:
            logging.debug('EMPTY response received')
        else:
            logging.debug('EXISTING response received: %s',
                          str(response_servers[-1]))

        logging.debug('NUMBER OF SERVERS: %d', len(servers))
        logging.debug('-' * 60)

        i += 1

    amqp_channel.close()
    amqp_connection.close()

def main():
    """ Query the master server and add the results to the database """
    usage = 'usage: masterserver.py [options]'
    parser = OptionParser(usage)
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="enable debug messages")
    
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error('incorrect number of arguments')

    logging.basicConfig(level=logging.DEBUG)
    if not options.debug:
        logging.disable(logging.DEBUG)

    # run through all the master servers we know of and ask them for ips
    for server_address in master_servers:
        run_full_query(server_address)

if __name__ == '__main__':
    main()
