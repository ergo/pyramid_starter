# -*- coding: utf-8 -*-
from __future__ import absolute_import
import structlog
import pyramid.httpexceptions
from pyramid.view import view_config, view_defaults
from ziggurat_foundations.models.services.group_permission import \
    GroupPermissionService

from testscaffold.models.group import Group
from testscaffold.models.group_permission import GroupPermission
from testscaffold.services.group import GroupService
from testscaffold.services.user import UserService
from testscaffold.validation.schemes import GroupEditSchema

log = structlog.getLogger(__name__)

GROUPS_PER_PAGE = 50


class GroupsShared(object):
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request

    def collection_list(self):
        groups = GroupService.all(Group, db_session=self.request.dbsession)
        return groups

    def group_get(self, obj_id):
        request = self.request
        group = GroupService.by_id(obj_id, db_session=request.dbsession)
        if not group:
            raise pyramid.httpexceptions.HTTPNotFound()
        return group

    def user_get(self, obj_id):
        request = self.request
        user = UserService.by_id(obj_id, db_session=request.dbsession)
        if not user:
            raise pyramid.httpexceptions.HTTPNotFound()
        return user

    def permission_get(self, group, permission):
        permission = GroupPermissionService.by_group_and_perm(
            group.id, permission, db_session=self.request.dbsession)
        if not permission:
            raise pyramid.httpexceptions.HTTPNotFound()
        return permission

    def populate_instance(self, instance, data):
        instance.populate_obj(data)
        log.info('group_populate_instance', action='updated')

    def delete(self, instance):
        log.info('group_delete', group_id=instance.id,
                 group_name=instance.group_name)
        instance.delete(self.request.dbsession)
        self.request.session.flash({'msg': 'Group removed.',
                                    'level': 'success'})

    def permission_post(self, group, permission):
        try:
            self.permission_get(group, permission)
        except pyramid.httpexceptions.HTTPNotFound:
            log.info('group_permission_post', group_id=group.id,
                     group_name=group.group_name, permission=permission)
            permission_inst = GroupPermission(perm_name=permission)
            group.permissions.append(permission_inst)
            self.request.session.flash({'msg': 'Permission granted for group.',
                                        'level': 'success'})
        return permission

    def permission_delete(self, group, permission):
        permission_inst = GroupPermissionService.by_group_and_perm(
            group.id, permission, db_session=self.request.dbsession)
        if permission_inst:
            log.info('group_permission_delete', group_id=group.id,
                     group_name=group.group_name, permission=permission)
            group.permissions.remove(permission_inst)
            self.request.session.flash(
                {'msg': 'Permission withdrawn from group.',
                 'level': 'success'})

    def user_post(self, group, user):
        if user not in group.users:
            group.users.append(user)
            self.request.session.flash({'msg': 'User added to group.',
                                        'level': 'success'})
            log.info('group_user_post', group_id=group.id, user=user.id,
                     group_name=group.group_name, user_name=user.user_name)

    def user_delete(self, group, user):
        if user in group.users:
            group.users.remove(user)
            self.request.session.flash({'msg': 'User removed from group.',
                                        'level': 'success'})
            log.info('group_user_delete', group_id=group.id, user_id=user.id,
                     group_name=group.group_name, user_name=user.user_name)


@view_defaults(route_name='api_object', renderer='json',
               match_param='object=groups',
               permission='admin_groups')
class GroupsAPI(object):
    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(route_name='api_objects', request_method='GET')
    def collection_list(self):
        group_paginator = self.base_view.collection_list()
        return [group for group in group_paginator.items]

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = GroupEditSchema(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        group = Group()
        self.base_view.populate_instance(group, data)
        group.persist(flush=True, db_session=self.request.dbsession)
        return group.get_dict()

    @view_config(request_method='GET')
    def get(self):
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        return group.get_dict()

    @view_config(request_method="PATCH")
    def patch(self):
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        schema = GroupEditSchema(context={'request': self.request,
                                          'modified_obj': group})
        data = schema.load(self.request.unsafe_json_body).data
        self.base_view.populate_instance(group, data)
        return group.get_dict()

    @view_config(request_method="DELETE")
    def delete(self):
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        self.base_view.delete(group)
        return ''


@view_defaults(route_name='api_object_relation', renderer='json',
               match_param=('object=groups', 'relation=permissions',),
               permission='admin_groups')
class GroupsPermissionsAPI(object):
    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(request_method="POST")
    def post(self):
        json_body = self.request.unsafe_json_body
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        self.base_view.permission_post(group, json_body['permission'])
        return group

    @view_config(request_method="DELETE")
    def delete(self):
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        permission = self.base_view.permission_get(
            group, self.request.GET.get('permission'))
        self.base_view.permission_delete(group, permission)
        return group


@view_defaults(route_name='api_object_relation', renderer='json',
               match_param=('object=groups', 'relation=users',),
               permission='admin_groups')
class GroupsUserRelationAPI(object):
    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(request_method="POST")
    def post(self):
        json_body = self.request.unsafe_json_body
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        user = self.base_view.user_get(json_body.get('id'))
        self.base_view.user_post(group, user)

    @view_config(request_method="DELETE")
    def delete(self):
        group = self.base_view.group_get(self.request.matchdict['object_id'])
        user = self.base_view.user_get(self.request.GET.get('user_id'))
        self.base_view.user_delete(group, user)
        return group
