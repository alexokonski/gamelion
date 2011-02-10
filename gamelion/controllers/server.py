import logging
import json
import socket
import threading
import sys

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gamelion.lib.base import BaseController, render
from gamelion.lib.queryserver import query_game_server
from gamelion.model import *

log = logging.getLogger(__name__)

class ServerController(BaseController):

    def index(self, address):
        address_list = address.split(':')

        if len(address_list) != 2:
            abort(400)

        ip, port = address_list
        try:
            port = int(port)
        except:
            abort(400)

        if 'json' in request.params:
            response.content_type = 'application/json'

            server_response = query_game_server(ip, port)

            if server_response != None:
                json_response = server_response.as_json_dict()
                print json_response
                return json.dumps(json_response)
            else:
                return json.dumps({ 'success' : False })

        c.server = Session.query(Server)\
                          .filter(Server.address == ip)\
                          .filter(Server.port == port)\
                          .one()

        return render("/server.mako")
