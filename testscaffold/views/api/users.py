# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from pyramid.view import view_config, view_defaults

from testscaffold.models.user import User
from testscaffold.util import safe_integer
from testscaffold.util.request import gen_pagination_headers
from testscaffold.validation.schemes import UserCreateSchema
from testscaffold.validation.schemes import UserEditSchema
from testscaffold.validation.schemes import UserSearchSchema
from testscaffold.views import BaseView
from testscaffold.views.shared.users import UsersShared

log = logging.getLogger(__name__)


@view_defaults(route_name='api_object', renderer='json',
               permission='admin_users',
               match_param=('object=users',))
class UserAPIView(BaseView):
    def __init__(self, request):
        super(UserAPIView, self).__init__(request)
        self.shared = UsersShared(request)

    @view_config(route_name='api_objects', request_method='GET')
    def collection_list(self):
        schema = UserCreateSchema(context={'request': self.request})
        page = safe_integer(self.request.GET.get('page', 1))
        filter_params = UserSearchSchema().load(self.request.GET.mixed()).data
        user_paginator = self.shared.collection_list(
            page=page, filter_params=filter_params
        )
        headers = gen_pagination_headers(request=self.request,
                                         paginator=user_paginator)
        self.request.response.headers.update(headers)
        return schema.dump(user_paginator.items, many=True).data

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = UserCreateSchema(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        user = User()
        self.shared.populate_instance(user, data)
        user.persist(flush=True, db_session=self.request.dbsession)
        return schema.dump(user).data

    @view_config(request_method='GET')
    def get(self):
        schema = UserCreateSchema(context={'request': self.request})
        user = self.shared.user_get(self.request.matchdict['object_id'])
        return schema.dump(user).data

    @view_config(request_method="PATCH")
    def patch(self):
        user = self.shared.user_get(self.request.matchdict['object_id'])
        schema = UserEditSchema(context={'request': self.request,
                                         'modified_obj': user})
        data = schema.load(self.request.unsafe_json_body, partial=True).data
        self.shared.populate_instance(user, data)
        return schema.dump(user).data

    @view_config(request_method="DELETE")
    def delete(self):
        user = self.shared.user_get(self.request.matchdict['object_id'])
        self.shared.delete(user)
        return True


@view_defaults(route_name='api_object_relation', renderer='json',
               match_param=('object=users', 'relation=permissions',),
               permission='admin_users')
class UsersPermissionsAPI(object):
    def __init__(self, request):
        self.request = request
        self.shared = UsersShared(request)

    @view_config(request_method="POST")
    def post(self):
        json_body = self.request.unsafe_json_body
        user = self.shared.user_get(self.request.matchdict['object_id'])
        self.shared.permission_post(user, json_body['perm_name'])
        return True

    @view_config(request_method="DELETE")
    def delete(self):
        user = self.shared.user_get(self.request.matchdict['object_id'])
        permission = self.shared.permission_get(
            user, self.request.GET.get('perm_name'))
        self.shared.permission_delete(user, permission)
        return True
