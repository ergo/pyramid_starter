# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults

from ziggurat_foundations.models.services.resource import ResourceService
from ziggurat_foundations import noop, noparent

from testscaffold.models.entry import Entry
from testscaffold.validation.schemes import EntryCreateSchemaAdmin
from testscaffold.views.shared.entries import EntriesShared
from testscaffold.util import safe_integer
from testscaffold.util.request import gen_pagination_headers
from testscaffold.services.resource_tree_service import tree_service

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
        schema = EntryCreateSchemaAdmin(context={'request': self.request})
        page = safe_integer(self.request.GET.get('page', 1))
        filter_params = self.request.GET.mixed()
        entries_paginator = self.shared.collection_list(
            page=page, filter_params=filter_params)
        headers = gen_pagination_headers(
            request=self.request, paginator=entries_paginator)
        self.request.response.headers.update(headers)
        return schema.dump(entries_paginator.items, many=True).data

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = EntryCreateSchemaAdmin(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        resource = Entry()
        self.shared.populate_instance(resource, data)
        resource.persist(flush=True, db_session=self.request.dbsession)
        position = data.get('ordering')
        if position is not None:
            tree_service.set_position(
                resource_id=resource.resource_id, to_position=position,
                db_session=self.request.dbsession)
        else:
            # this accounts for the newly inserted row so the total_children
            # will be max+1 position for new row
            total_children = tree_service.count_children(
                resource.parent_id, db_session=self.request.dbsession)
            tree_service.set_position(
                resource_id=resource.resource_id, to_position=total_children,
                db_session=self.request.dbsession)
        return schema.dump(resource).data

    @view_config(request_method="PATCH")
    def patch(self):
        entry = self.shared.entry_get(self.request.matchdict['object_id'])
        schema = EntryCreateSchemaAdmin(
            context={'request': self.request, 'modified_obj': entry})
        data = schema.load(self.request.unsafe_json_body, partial=True).data
        # we need to ensure we are not overwriting the values
        # before move_to_position is invoked
        ordering = data.pop('ordering', noop)
        parent_id = data.pop('parent_id', noparent)
        self.shared.populate_instance(entry, data)
        if ordering is not noop or parent_id is not noparent:
            tree_service.move_to_position(
                resource_id=entry.resource_id, new_parent_id=parent_id,
                to_position=ordering, db_session=self.request.dbsession)
        return schema.dump(entry).data

    @view_config(request_method="DELETE")
    def delete(self):
        entry = self.shared.entry_get(self.request.matchdict['object_id'])
        tree_service.delete_branch(
            entry.resource_id, db_session=self.request.dbsession)
        return True
