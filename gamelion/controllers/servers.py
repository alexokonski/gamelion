import logging

import formencode.htmlfill
from formencode import htmlfill

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate

from gamelion.lib.base import BaseController, render
from gamelion.model import *
import webhelpers.paginate as paginate

log = logging.getLogger(__name__)

class ServersController(BaseController):

    def nono(self):
        return 'That\'s a nono'

    @validate(
        schema=SearchForm(), 
        form='nono', 
        post_only=False,
        on_get=True
    )
    def index(self):
        likeString = '%'

        # build search query
        if 'search' in request.params:
            likeString = '%' + request.params['search'] + '%'

        serverQuery = Session.query(Server)\
                         .filter(Server.name != None)\
                         .filter(Server.name.like(likeString))\
                         .order_by(Server.name)

        app_ids = self.form_result['game']

        # restrict the query to certain games (if applicable)
        if len(app_ids) > 0:
            serverQuery = serverQuery.filter(Server.app_id.in_(app_ids))

        # checkboxes will be generated from this list
        c.app_ids = GetValidAppIds() 

        # make sure the paginator links have the currently filtered
        # games in them
        kwargs = {}
        i = 0
        for id in c.app_ids:
            param_name = 'game-%d' % i
            if param_name in request.params:
                kwargs[param_name] = id
            i += 1
 
        c.paginator = paginate.Page(
            serverQuery,
            item_count=serverQuery.count(),
            page=int(request.params.get('page', 1)),
            items_per_page=50,
            search=request.params.get('search', ''),
            **kwargs
        )

        renderedMako = render('/servers.mako')
        return htmlfill.render(renderedMako, defaults=request.params)

