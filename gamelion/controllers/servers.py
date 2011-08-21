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

        checkbox_groups = form.get_checkbox_groups()
        kwargs = {}
        for group in checkbox_groups:
            serverQuery = group.apply_filter(serverQuery, self.form_result)
        
            # make sure the paginator links have the currently filtered
            # checkboxes in them
            for checkbox in group.checkboxes:
                if checkbox.name in request.params:
                    kwargs[checkbox.name] = checkbox.value

        c.checkbox_groups = checkbox_groups

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

