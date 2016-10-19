# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults

from testscaffold.models.resource import Resource
from testscaffold.validation.schemes import EntryCreateSchema

log = logging.getLogger(__name__)


@view_defaults(route_name='api_object', renderer='json',
               permission='admin_users',
               match_param=('object=entries',))
class EntriesAPIView(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = EntryCreateSchema(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        resource = Resource()
        self.base_view.populate_instance(resource, data)
        resource.persist(flush=True, db_session=self.request.dbsession)
        return schema.dump(resource).data