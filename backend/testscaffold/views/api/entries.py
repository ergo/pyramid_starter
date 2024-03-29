# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults
from ziggurat_foundations import noop

from testscaffold.models.db import Entry
from testscaffold.services.resource_tree_service import tree_service
from testscaffold.util import safe_integer
from testscaffold.util.request import gen_pagination_headers
from testscaffold.validation.schemes import EntryCreateSchema
from testscaffold.views import BaseView
from testscaffold.views.shared.entries import EntriesShared
from testscaffold.views.shared.resources import ResourcesShared

log = logging.getLogger(__name__)


@view_defaults(
    route_name="api_object", renderer="json", permission="admin_users", match_param=("object=entries",),
)
class EntriesAPIView(BaseView):
    """
    Views for entry type resources
    """

    def __init__(self, request):
        super(EntriesAPIView, self).__init__(request)
        self.shared = EntriesShared(request)
        self.resources_shared = ResourcesShared(request)

    @view_config(route_name="api_objects", request_method="GET")
    def collection_list(self):
        schema = EntryCreateSchema(context={"request": self.request})
        page = safe_integer(self.request.GET.get("page", 1))
        filter_params = self.request.GET.mixed()
        entries_paginator = self.shared.collection_list(page=page, filter_params=filter_params)
        headers = gen_pagination_headers(request=self.request, paginator=entries_paginator)
        self.request.response.headers.update(headers)
        return schema.dump(entries_paginator.items, many=True)

    @view_config(route_name="api_objects", request_method="POST")
    def post(self):
        schema = EntryCreateSchema(context={"request": self.request})
        data = schema.load(self.request.unsafe_json_body)
        resource = Entry()
        self.shared.populate_instance(resource, data)
        self.request.user.resources.append(resource)
        resource.persist(flush=True, db_session=self.request.dbsession)
        position = data.get("ordering") or noop
        if position is not noop:
            tree_service.set_position(
                resource_id=resource.resource_id, to_position=position, db_session=self.request.dbsession,
            )
        else:
            # this accounts for the newly inserted row so the total_children
            # will be max+1 position for new row
            total_children = tree_service.count_children(resource.parent_id, db_session=self.request.dbsession)
            tree_service.set_position(
                resource_id=resource.resource_id, to_position=total_children, db_session=self.request.dbsession,
            )
        return schema.dump(resource)

    @view_config(request_method="PATCH", permission="owner")
    def patch(self):
        resource = self.shared.entry_get(self.request.matchdict["object_id"])
        schema = EntryCreateSchema(context={"request": self.request, "modified_obj": resource})
        data = schema.load(self.request.unsafe_json_body, partial=True)
        # we need to ensure we are not overwriting the values
        # before move_to_position is invoked
        position = data.pop("ordering", None) or noop
        parent_id = data.pop("parent_id", None) or noop
        self.shared.populate_instance(resource, data, exclude_keys=["ordering", "parent_id"])
        into_new_parent = parent_id != resource.parent_id and parent_id is not noop
        if position is not noop or into_new_parent:
            if not position and into_new_parent:
                position = tree_service.count_children(parent_id, db_session=self.request.dbsession) + 1
            tree_service.move_to_position(
                resource_id=resource.resource_id,
                new_parent_id=parent_id,
                to_position=position,
                db_session=self.request.dbsession,
            )
        return schema.dump(resource)

    @view_config(request_method="DELETE", permission="owner")
    def delete(self):
        instance = self.shared.entry_get(self.request.matchdict["object_id"])

        log.info(
            "resource_delete", extra={"resource_id": instance.resource_id, "resource_name": instance.resource_name,},
        )
        # self.request.session.flash(
        #     {'msg': self.translate(_('Resource removed.')),
        #      'level': 'success'})

        tree_service.delete_branch(instance.resource_id, db_session=self.request.dbsession)
        return True
