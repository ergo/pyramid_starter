# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults

log = logging.getLogger(__name__)


@view_defaults(route_name='objects', permission='authenticated')
class UserPage(object):
    def __init__(self, request):
        self.request = request

    @view_config(renderer='testscaffold:templates/user/index.jinja2',
                 match_param=('object=user_self', 'verb=GET'))
    def index(self):
        return {'user': self.request.user}


@view_defaults(route_name='object_relation', renderer='json',
               permission='authenticated')
class GroupsUserRelationAPI(object):
    def __init__(self, request):
        self.request = request

    @view_config(renderer='testscaffold:templates/user/auth_tokens.jinja2',
                 match_param=('object=user_self', 'relation=auth_tokens',
                              'verb=GET'))
    def auth_tokens(self):
        auth_tokens = []
        return {'auth_tokens': auth_tokens}
