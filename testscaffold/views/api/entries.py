# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults

from testscaffold.models.entry import Entry
from testscaffold.validation.schemes import EntryCreateSchema
from testscaffold.views.shared.entries import EntriesShared

log = logging.getLogger(__name__)


@view_defaults(route_name='api_object', renderer='json',
               permission='admin_users',
               match_param=('object=entries',))
class EntriesAPIView(object):
    def __init__(self, request):
        self.request = request
        self.shared = EntriesShared(request)

    @view_config(route_name='api_objects', request_method='GET')
    def collection_list(self):
        schema = EntryCreateSchema(context={'request': self.request})
        entries_paginator = self.shared.collection_list()
        return schema.dump(entries_paginator.items, many=True).data

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = EntryCreateSchema(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        resource = Entry()
        self.shared.populate_instance(resource, data)
        resource.persist(flush=True, db_session=self.request.dbsession)
        return schema.dump(resource).data