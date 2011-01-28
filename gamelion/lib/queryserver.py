import socket
import struct as pystruct
import gamelion.lib.stringz as struct
import logging

class QueryResult(object):
    def __init__(self, raw_response):
        header, = struct.unpack('<i', raw_response)
        raw_response = raw_response[pystruct.calcsize('i'):]
        assert header == -1

        # unpack the rest of the data
        _,\
        _,\
        self._name,\
        _,\
        _,\
        self._title,\
        self._app_id,\
        self._players,\
        self._max_players = struct.unpack('<cczzzzhBB', raw_response)

    def as_json_dict(self):
        return {
            'players'     : self._players,
            'max_players' : self._max_players
        }

def query_game_server(address, port):
    query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query_socket.settimeout(2.0)

    data = struct.pack('<icz', -1, 'T', 'Source Engine Query')
    
    try:
        query_socket.sendto(data, (address, port))
    except (socket.timeout, socket.error, socket.herror, socket.gaierror) as detail:
        logging.error('query_server sendto socket exception: %s', detail)

    retries = 0
    response = ''
    while retries < 3:
        try:
            response = query_socket.recv(2048)
            break
        except socket.timeout:
            retries += 1
        except (socket.error, socket.herror, socket.gaierror) as detail:
            logging.error('query_server recv socket exception: %s', detail)
            return
    if response != '':
        return QueryResult(response)
    else:
        return None

