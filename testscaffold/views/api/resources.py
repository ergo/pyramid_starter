# -*- coding: utf-8 -*-

from __future__ import absolute_import

from pyramid.view import view_config, view_defaults
from ziggurat_foundations.models.services.user import UserService

from testscaffold.validation.schemes import (
    UserResourcePermissionSchema,
    GroupResourcePermissionSchema,
)
from testscaffold.views.shared.resources import ResourcesShared


@view_defaults(route_name='api_object_relation', renderer='json',
               match_param=('object=resources', 'relation=user_permissions',),
               permission='owner')
class ResourcesUserPermissionsAPI(object):
    def __init__(self, request):
        self.request = request
        self.shared = ResourcesShared(request)

    @view_config(request_method="POST")
    def post(self):
        resource = self.request.context.resource

        schema = UserResourcePermissionSchema(
            context={'request': self.request,
                     'resource': resource})
        data = schema.load(self.request.unsafe_json_body).data
        user = UserService.by_user_name(
            data['user_name'], db_session=self.request.dbsession)
        perm_inst = self.shared.user_permission_post(
            resource, user.id, data['perm_name'])
        self.request.dbsession.flush()
        return perm_inst.get_dict()

    @view_config(request_method="DELETE")
    def delete(self):
        resource = self.request.context.resource

        schema = UserResourcePermissionSchema(
            context={'request': self.request,
                     'resource': resource})
        params = {'user_name': self.request.GET.get('user_name'),
                  'perm_name': self.request.GET.get('perm_name')}
        data = schema.load(params).data
        user = UserService.by_user_name(
            data['user_name'], db_session=self.request.dbsession)
        self.shared.user_permission_delete(
            resource, user.id, data['perm_name'], )
        return True


@view_defaults(route_name='api_object_relation', renderer='json',
               match_param=('object=resources', 'relation=group_permissions',),
               permission='owner')
class ResourcesGroupPermissionsAPI(object):
    def __init__(self, request):
        self.request = request
        self.shared = ResourcesShared(request)

    @view_config(request_method="POST")
    def post(self):
        resource = self.request.context.resource

        schema = GroupResourcePermissionSchema(
            context={'request': self.request,
                     'resource': resource})
        data = schema.load(self.request.unsafe_json_body).data
        perm_inst = self.shared.group_permission_post(
            resource, data['group_id'], data['perm_name'])
        self.request.dbsession.flush()
        return perm_inst.get_dict()

    @view_config(request_method="DELETE")
    def delete(self):
        resource = self.request.context.resource

        schema = GroupResourcePermissionSchema(
            context={'request': self.request,
                     'resource': resource})
        params = {'group_id': self.request.GET.get('group_id'),
                  'perm_name': self.request.GET.get('perm_name')}
        data = schema.load(params).data
        self.shared.group_permission_delete(
            resource, data['group_id'], data['perm_name'])
        return True
