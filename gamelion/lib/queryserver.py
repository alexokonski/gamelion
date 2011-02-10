import socket
import struct as pystruct
import gamelion.lib.stringz as struct
import logging

class ServerPlayer(object):
    def __init__(self, name, kills, time_connected):
        self.name = name
        self.kills = kills
        self.time_connected = time_connected
    
    def as_json_dict(self):
        return {
            'name'           : self.name,
            'kills'          : self.kills,
            'time_connected' : self.time_connected
        }

class InfoResponse(object):
    def __init__(self, info_response):
        if info_response != None:
            header, = struct.unpack('<i', info_response)
            info_response = info_response[pystruct.calcsize('<i'):]
            assert header == -1

            # unpack the info response
            _,\
            _,\
            self.name,\
            self.map,\
            _,\
            self.description,\
            self.app_id,\
            self.number_of_players,\
            self.max_players,\
            self.number_of_bots,\
            self.is_dedicated,\
            self.operating_system,\
            self.password_required,\
            self.is_secure,\
            self.version,\
                    = struct.unpack('<cczzzzhBBBccBBz', info_response)

    def fill_server(self, server):
        server.name = unicode(self.name, encoding='latin_1')
        server.map = unicode(self.map, encoding='latin_1')
        server.app_id = self.app_id
        server.number_of_players = self.number_of_players
        server.max_players = self.max_players
        server.number_of_bots = self.number_of_bots
        server.is_dedicated = self.is_dedicated
        server.operating_system = self.operating_system
        server.password_required = self.password_required
        server.is_secure = self.is_secure
        server.version = self.version

class PlayerResponse(object):
    def __init__(self, player_response):
        self.players = []
        if player_response != None: 
            pre_header,\
            header,\
            num_players = struct.unpack('<IBB', player_response)
            assert header == 0x44

            player_response = player_response[pystruct.calcsize('<IBB'):]

            # unpack all the players in the player response
            while len(player_response) > 0:
                index,\
                name,\
                kills,\
                time = struct.unpack('<BzIf', player_response)
                
                self.players.append(ServerPlayer(name, kills, time))

                # add 1 for null byte 
                packet_size = pystruct.calcsize('<BIf') + len(name) + 1
                player_response = player_response[packet_size:]

            assert len(self.players) == num_players
    
class QueryResult(object):
    def __init__(self, info_response=None, player_response=None):
        self._info_response = InfoResponse(info_response)
        self._player_response = PlayerResponse(player_response)

    def as_json_dict(self):
        return {
            'map'               : self._info_response.map,
            'number_of_players' : self._info_response.number_of_players,
            'max_players'       : self._info_response.max_players,
            'number_of_bots'    : self._info_response.number_of_bots,
            'is_dedicated'      : self._info_response.is_dedicated,
            'os'                : self._info_response.operating_system,
            'password_required' : self._info_response.password_required,
            'is_secure'         : self._info_response.is_secure,
            'version'           : self._info_response.version,
            'players'           :
                [p.as_json_dict() for p in self._player_response.players]
        }

def try_query(ip, port, data):
    MAX_RETRIES = 3
    query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query_socket.settimeout(2.0)
    
    retries = 0
    response = None 
    while retries < MAX_RETRIES:
        try:
            query_socket.sendto(data, (ip, port))
            response = query_socket.recv(2048)
            break
        except socket.timeout:
            retries += 1
        except (socket.error, socket.herror, socket.gaierror) as detail:
            logging.error('recv socket exception: %s', detail)
            return None

    return response

def pack_player_query(challenge):
    return struct.pack('<IBi', 0xFFFFFFFF, 0x55, challenge)

def query_game_server(ip, port):
    # retrieve a server info query
    server_query = struct.pack('<icz', -1, 'T', 'Source Engine Query')
    info_response = try_query(ip, port, server_query)

    # retrieve a player query - first we have to get the challenge number
    challenge_query = pack_player_query(-1)
    challenge_response = try_query(ip, port, challenge_query)
    player_response = None

    # now we have a challenge response - get the actual player list
    if challenge_response != None:
        pre_header,\
        header,\
        challenge = struct.unpack('<IBi', challenge_response)
        assert header == 0x41

        player_query = pack_player_query(challenge)
        player_response = try_query(ip, port, player_query)
        print 'challenge_response:', repr(challenge_response)
        print 'player_response:', repr(player_response)

    if player_response == None and info_response == None:
        return None
    else:
        return QueryResult(info_response=info_response, 
                           player_response=player_response)

