import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gamelion.lib.base import BaseController, render
from gamelion.model import *

log = logging.getLogger(__name__)

class ServersController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/servers.mako')
        # or, return a string

        c.servers = Session.query(Server).filter(Server.name != None).all()
        return render('/servers.mako')
