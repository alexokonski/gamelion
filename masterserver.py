"""
masterserver.py

Runs a Master Server query for Valve games using the protocol specified in:
http://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol

It then adds the results to the database.  This script is designed 
to be run as a cron job
"""

from gamelion.model import *
import gamelion.lib.stringz as struct
import struct as pystruct
import socket
import time
import logging
from optparse import OptionParser
from kombu.connection import BrokerConnection
from kombu.messaging import Exchange, Queue, Producer

master_servers = [ ('72.165.61.153', 27015),
                   ('72.165.61.189', 27010),
                   ('68.142.72.250', 27012) ]

MESSAGE_BATCH_SIZE = 100

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

def unpack_response(response, producer):
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
        # package up the ip/port
        #headers = {
        #    'ip': ip_string,
        #    'port': port
        #}

        # delivery_mode=1 means no ack necessary
        body = "%s:%s" % (ip_string, port)
        producer.publish(body=body, delivery_mode=1, serializer=None)

        ips.append((ip_string, port))

    assert len(response) == 0

    return ips

def run_full_query(server_address, producer):
    """ Run a full master server query """

    DEFAULT_IP = ('0.0.0.0', 0)
    MAX_ITERATIONS = 10000
    MAX_TIMEOUTS = 5

    #servers = set()
    previous_server = DEFAULT_IP

    i = 0
    timeouts = 0
    num_servers = 0
    # get all the ips the master server wishes to give us
    while i < MAX_ITERATIONS and\
          (i == 0 or previous_server != DEFAULT_IP) and\
          timeouts < MAX_TIMEOUTS:

        logging.debug('')
        logging.debug('-' * 60)

        # get a string for the last ip the server sent us
        server_string = '%s:%d' % (previous_server)
        query_data = pack_query(0xFF, server_string, r'\napp\500')

        # Tell the server we'd like some data
        query_server(server_address, query_data)

        # Wait to hear back, and add the results to the list
        response = receive_response()
        response_servers = unpack_response(response, producer)
        
        #if len(response_servers) > 0: and\
           #response_servers[-1] not in servers:
        if len(response) > 0:

            timeouts = 0
            response_servers = unpack_response(response, producer)
            previous_server = response_servers[-1]

            # We just got a list that (presumably) we haven't
            # seen yet.  Grab the last one to use as the next 'seed'
            '''previous_server = response_servers[-1]
            if previous_server == DEFAULT_IP:
                break

            # add these servers to the queue
            for ip, port in response_servers:
                #logging.debug('SENDING %s, %d', ip, port)

                # package up the ip/port
                headers = {
                    'ip': ip,
                    'port': port
                }

                # delivery_mode=1 means no ack necessary
                producer.publish(headers, delivery_mode=1)'''
            
            length = len(response_servers)
            logging.debug('SENT %d MESSAGES', length)
            num_servers += length
            # update our list of servers so we'll be able to know if 
            # we get another new list
            #servers.update(response_servers)

        elif len(response_servers) == 0:
            timeouts += 1
            logging.debug('EMPTY response received')
        else:
            timeouts = 0
            logging.debug('EXISTING response received: %s',
                          str(response_servers[-1]))

        logging.debug('NUMBER OF SERVERS: %d', num_servers)
        logging.debug('-' * 60)

        i += 1

        # this loop has a tendency to spin fast
        time.sleep(1)

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

    # declare exchange
    server_exchange = Exchange('servers', type='fanout')
    
    # set up our amqp connection
    connection = BrokerConnection(
        hostname='localhost', 
        userid='alex', 
        password='alex',
        virtual_host='/'
    )
    channel = connection.channel()
    
    producer = Producer(channel, server_exchange, serializer="pickle")
    # run through all the master servers we know of and ask them for ips
    for server_address in master_servers:
        logging.debug('*' * 60)
        logging.debug('NEW SERVER: %s', str(server_address))
        logging.debug('*' * 60)

        run_full_query(server_address, producer)
    
    channel.close()
    connection.release()

if __name__ == '__main__':
    main()
