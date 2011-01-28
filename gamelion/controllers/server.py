import logging
import json
import socket
import threading
import sys

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gamelion.lib.base import BaseController, render
from gamelion.lib.queryserver import query_game_server

log = logging.getLogger(__name__)

class ServerController(BaseController):

    def index(self, address):
        if 'json' in request.params:
            print request.params
            response.content_type = 'application/json'

            address_list = address.split(':')
            print address_list

            server_response = None 
            if len(address_list) == 2:
                ip, port = address_list
                server_response = query_game_server(ip, int(port))

            if server_response != None:
                json_response = server_response.as_json_dict()
                json_response['success'] = True
                return json.dumps(json_response)
            else:
                return json.dumps({ 'success' : False })
        
        return render("/server.mako")
