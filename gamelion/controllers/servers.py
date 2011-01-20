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

        # build search query
        if 'search' in request.params:
            likeString = '%' + request.params['search'] + '%'

        # figure out which games we want to search within
        checkbox_to_app_id = {
            'cs1.6': 10,
            'css'  : 240,
            'tf2'  : 440
        }

        games_requested = filter(lambda x: x in request.params, 
                                 checkbox_to_app_id)

        or_list = ['app_id=%d' % checkbox_to_app_id[x]\
                   for x in games_requested]

        or_string = ' OR '.join(or_list)

        # the query will always look like this...
        serverQuery = Session.query(Server)\
                         .filter(Server.name != None)\
                         .filter(Server.name.like(likeString))\
                         .order_by(Server.name)

        # ... unless we've restricted our search to certain games only
        if or_string != '':
            serverQuery = serverQuery.filter(or_string) 

        kwargs = {'search': request.params.get('search','')}
        for game in games_requested:
            kwargs[game] = ''
        
        c.paginator = paginate.Page(
            serverQuery,
            item_count=serverQuery.count(),
            page=int(request.params.get('page', 1)),
            items_per_page=50,
            **kwargs
        )

        return render('/servers.mako')

