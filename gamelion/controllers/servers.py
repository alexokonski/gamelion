import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gamelion.lib.base import BaseController, render
from gamelion.model import *

log = logging.getLogger(__name__)

class ServersController(BaseController):

    def index(self):
        likeString = '%'

        if 'search' in request.params:
            likeString = '%' + request.params['search'] + '%'

        c.servers = Session.query(Server)\
                           .filter(Server.name != None\
                                    and Server.name.like(likeString))\
                           .all()

        return render('/servers.mako')

