import logging

import formencode.htmlfill
from formencode import htmlfill

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate

from gamelion.lib.base import BaseController, render
from gamelion.model import *
import webhelpers.paginate as paginate
from gamelion.lib.queryserver import get_time_string
import datetime
from sqlalchemy import desc

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
                         .filter(Server.name.ilike(likeString))\
                         .order_by(desc(Server.timestamp))

        filtered_app_ids = self.form_result['game']

        searchable_apps = form.get_searchable_apps()
        all_app_ids = [app.app_id for app in searchable_apps]

        # restrict the query to certain games (if applicable)
        if len(filtered_app_ids) > 0:
            serverQuery = serverQuery.filter(
                Server.app_id.in_(filtered_app_ids)
            )
        else:
            serverQuery = serverQuery\
                            .filter(Server.app_id.in_(all_app_ids))

        # app (game) checkboxes will be generated from this list
        c.app_ids = searchable_apps 
        c.NUM_PRIMARY_CHECK_BOXES = form.NUM_PRIMARY_CHECK_BOXES

        # make sure the paginator links have the currently filtered
        # games in them
        kwargs = {}
        i = 0
        for id in all_app_ids:
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

