import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gamelion.lib.base import BaseController, render
from gamelion.model import *
import webhelpers.paginate as paginate

log = logging.getLogger(__name__)

class ServersController(BaseController):

    def index(self):
        likeString = '%'

        if 'search' in request.params:
            likeString = '%' + request.params['search'] + '%'

        serverQuery = Session.query(Server)\
                         .filter(Server.name != None and 
                                 Server.name.like(likeString))\
                         .order_by(Server.name)
                         
        c.paginator = paginate.Page(
            serverQuery,
            item_count=serverQuery.count(),
            page=int(request.params.get('page', 1)),
            items_per_page=50,
            search=request.params.get('search', ''),
        )

        return render('/servers.mako')

