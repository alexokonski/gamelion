import socket
import struct as pystruct
import gamelion.lib.stringz as struct
import logging
from datetime import datetime
from gamelion.model import *

# http://darklaunch.com/2009/10/06/python-time-duration-human-friendly-timestamp
def get_time_string(seconds, significant_only=False):
    seconds = long(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)
 
    minutes = long(minutes)
    hours = long(hours)
    days = long(days)
    years = long(years)
 
    duration = []
    if years > 0 and (not significant_only or len(duration) == 0):
        duration.append('%d year' % years + 's'*(years != 1))
    else:
        if days > 0 and (not significant_only or len(duration) == 0):
            duration.append('%d day' % days + 's'*(days != 1))
        if hours > 0 and (not significant_only or len(duration) == 0):
            duration.append('%d hour' % hours + 's'*(hours != 1))
        if minutes > 0 and (not significant_only or len(duration) == 0):
            duration.append('%d minute' % minutes + 's'*(minutes != 1))
        if seconds > 0 and (not significant_only or len(duration) == 0):
            duration.append('%d second' % seconds + 's'*(seconds != 1))

    return ' '.join(duration)


class ServerPlayer(object):
    def __init__(self, name, kills, time_connected):
        self.name = name
        self.kills = kills
        self.time_connected = time_connected
    
    def as_json_dict(self):

        return { 
            'name'           : self.name,
            'kills'          : self.kills,
            'time_connected' : get_time_string(self.time_connected)
        }

    def __repr__(self):
        return 'ServerPlayer(%s, %d, %f)' % \
                (self.name, self.kills, self.time_connected)

    def __cmp__(self, other):
        return cmp(self.kills, other.kills) 


class InfoResponse(object):
    def __init__(self, info_response):
        if info_response != None:
            header, = struct.unpack('<i', info_response)
            info_response = info_response[pystruct.calcsize('<i'):]
            assert header == -1

            type, = struct.unpack('<c', info_response)

            #if this is a different kind of response, leave
            if type != 'I':
                raise Exception('INVALID PACKET, HEADER BYTE: %s' % (type,))

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

            self.name = self.name.strip()
            if len(self.name) == 0:
                self.name = '__NO_NAME__'

    def fill_server(self, server):
        MAX_NAME_LENGTH = Server.name.property.columns[0].type.length
        MAX_MAP_LENGTH = Server.map.property.columns[0].type.length
        MAX_VERSION_LENGTH = Server.version.property.columns[0].type.length

        server.name = unicode(
            self.name[:MAX_NAME_LENGTH], 
            encoding='latin_1'
        )

        server.map = unicode(self.map[:MAX_MAP_LENGTH], encoding='latin_1')
        server.app_id = self.app_id
        server.number_of_players = self.number_of_players
        server.max_players = self.max_players
        server.number_of_bots = self.number_of_bots
        server.is_dedicated = self.is_dedicated
        server.operating_system = self.operating_system

        if self.password_required == 0:
            server.password_required = False
        else:
            server.password_required = True

        if self.is_secure == 0:
            server.is_secure = False
        else:
            server.is_secure = True

        server.version = unicode(
            self.version[:MAX_VERSION_LENGTH], 
            encoding='latin_1'
        )
        
        # reset consecutive timeouts counter
        server.timeouts = 0

        # stamp with timestamp
        server.timestamp = datetime.now()

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
                time = struct.unpack('<Bzif', player_response)
           
                # don't include 'players' with no name - the steam
                # browser itself appears to ignore these
                if len(name) > 0:
                    self.players.append(ServerPlayer(name, kills, time))

                # add 1 for null byte in the player name 
                packet_size = pystruct.calcsize('<Bif') + len(name) + 1
                player_response = player_response[packet_size:]

            self.players.sort(reverse=True)

class QueryResult(object):
    def __init__(self, info_response=None, player_response=None):
        self._info_response = InfoResponse(info_response)
        self._player_response = PlayerResponse(player_response)

    def as_json_dict(self):
        is_secure = 'No'
        if self._info_response.is_secure:
            is_secure = 'Yes'

        password_required = 'No'
        if self._info_response.password_required:
            password_required = 'Yes'

        operating_system = 'Linux'
        if self._info_response.operating_system == 'w':
            operating_system = 'Windows'

        return {
            'map'               : self._info_response.map,
            'number_of_players' : self._info_response.number_of_players,
            'max_players'       : self._info_response.max_players,
            'number_of_bots'    : self._info_response.number_of_bots,
            'is_dedicated'      : self._info_response.is_dedicated,
            'os'                : operating_system,
            'password_required' : password_required,
            'is_secure'         : is_secure,
            'version'           : self._info_response.version,
            'players'           :
                [p.as_json_dict() for p in self._player_response.players]
        }

    def fill_server(self, server):
        self._info_response.fill_server(server)

def try_query(ip, port, data):
    MAX_RETRIES = 3
    query_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    query_socket.settimeout(5.0)
    
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

    if player_response == None and info_response == None:
        return None
    else:
        return QueryResult(info_response=info_response, 
                           player_response=player_response)

