# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import structlog
from pyramid.view import view_config, view_defaults
from testscaffold.models.resource import Resource

log = structlog.getLogger(__name__)


@view_defaults(route_name='api_object', renderer='json',
               permission='resources', match_param=('object=entries',))
class EntriesAPIView(object):
    def __init__(self, request):
        self.request = request

    def test(self):
        return {'A': 1, 'B': 2}
