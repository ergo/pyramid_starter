# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import pyramid.httpexceptions

from pyramid.view import view_config, view_defaults
from testscaffold.grids import GroupsGrid, UsersGroupsGrid, \
    GroupPermissionsGrid

from testscaffold.util import safe_integer
from testscaffold.models.group import Group
from testscaffold.services.group import GroupService
from testscaffold.validation.forms import GroupUpdateForm, GroupPermissionForm
from testscaffold.views.api.groups import GroupsShared, GROUPS_PER_PAGE

log = logging.getLogger(__name__)


class SharedRendererVars(object):
    def __init__(self, request, base_view):
        self.group = base_view.group_get(request.matchdict['object_id'])
        self.group_form = GroupUpdateForm(
            request.POST, obj=self.group,
            context={'request': request, 'modified_obj': self.group})
        self.permission_form = GroupPermissionForm(
            request.POST, context={'request': request})

        self.permissions_grid = GroupPermissionsGrid(self.group.permissions,
                                                     request=request,
                                                     group=self.group)


@view_defaults(route_name='admin_objects', permission='admin_groups')
class AdminGroupsView(object):
    """
    Handles group list and new group form
    """

    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(renderer='testscaffold:templates/admin/groups/index.jinja2',
                 match_param=('object=groups', 'verb=GET'))
    def collection_list(self):
        groups = self.base_view.collection_list()
        groups_grid = GroupsGrid(groups, request=self.request)
        return {'groups': groups,
                'groups_grid': groups_grid}

    @view_config(renderer='testscaffold:templates/admin/groups/edit.jinja2',
                 match_param=('object=groups', 'verb=POST'))
    def groups_post(self):
        request = self.request
        group = Group()
        group_form = GroupUpdateForm(
            request.POST, context={'request': request})

        if request.method == "POST" and group_form.validate():
            self.base_view.populate_instance(group, group_form.data)
            group.persist(flush=True, db_session=request.dbsession)
            log.info('groups_post', extra={'group_id': group.id,
                                           'group_name': group.group_name})
            request.session.flash({'msg': 'Group created.',
                                   'level': 'success'})
            location = request.route_url('admin_objects', object='groups',
                                         verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=location)

        return {"group": group,
                "group_form": group_form}


@view_defaults(route_name='admin_object', permission='admin_groups')
class AdminGroupView(object):
    """
    Handles operations on individual group
    """

    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(renderer='testscaffold:templates/admin/groups/edit.jinja2',
                 match_param=('object=groups', 'verb=GET'), )
    @view_config(renderer='testscaffold:templates/admin/groups/edit.jinja2',
                 match_param=('object=groups', 'verb=PATCH'))
    def group_get_patch(self):
        request = self.request
        shared = SharedRendererVars(request, self.base_view)
        if request.method == "POST" and shared.group_form.validate():
            self.base_view.populate_instance(shared.group,
                                             shared.group_form.data)
            request.session.flash({'msg': 'Group updated.',
                                   'level': 'success'})
            url = request.route_url(
                'admin_object', object='groups',
                object_id=shared.group.id, verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=url)

        return {'group': shared.group,
                'group_form': shared.group_form,
                'permission_form': shared.permission_form,
                'permissions_grid': shared.permissions_grid}

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'verb=DELETE'),
        request_method='GET')
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'verb=DELETE'),
        request_method='POST')
    def group_delete(self):
        request = self.request
        group = self.base_view.group_get(request.matchdict['object_id'])
        back_url = request.route_url('admin_objects', object='groups',
                                     verb='GET')

        if request.method == "POST":
            self.base_view.delete(group)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {"parent_obj": group,
                "member_obj": None,
                "confirm_url": request.current_route_url(),
                "back_url": back_url
                }


@view_defaults(route_name='admin_object_relation', permission='admin_groups')
class AdminGroupRelationsView(object):
    """
    Handles operations on group properties
    """

    def __init__(self, request):
        self.request = request
        self.base_view = GroupsShared(request)

    @view_config(
        renderer='testscaffold:templates/admin/groups/users_list.jinja2',
        match_param=['object=groups', 'relation=users', 'verb=GET'])
    def users_get(self):
        request = self.request
        group = self.base_view.group_get(request.matchdict['object_id'])
        page = safe_integer(request.GET.get('page', 1))

        user_paginator = GroupService.get_user_paginator(
            group,
            page=page,
            items_per_page=GROUPS_PER_PAGE,
            url_maker=lambda p: request.current_route_url(
                _query={"page": p}),
            db_session=request.dbsession
        )

        user_grid = UsersGroupsGrid(
            user_paginator, columns=["_numbered", "user_name", "email",
                                     "registered_date", "options"],
            start_number=GROUPS_PER_PAGE * (page - 1) or 1,
            request=request, group=group)
        return {"group": group,
                "user_grid": user_grid}

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'relation=users',
                     'verb=DELETE'),
        request_method="GET")
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'relation=users',
                     'verb=DELETE'),
        request_method="POST")
    def user_delete(self):
        request = self.request
        group = self.base_view.group_get(request.matchdict['object_id'])
        user = self.base_view.user_get(request.GET.get('user_id'))
        back_url = request.route_url(
            'admin_object_relation', object='groups', object_id=group.id,
            relation='users', verb='GET')

        if request.method == "POST":
            self.base_view.user_delete(group, user)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {"parent_obj": group,
                "member_obj": user,
                "confirm_url": request.current_route_url(),
                "back_url": back_url
                }

    @view_config(renderer='testscaffold:templates/admin/groups/edit.jinja2',
                 match_param=['object=groups', 'relation=permissions',
                              'verb=POST'])
    def permission_post(self):
        request = self.request
        shared = SharedRendererVars(request, self.base_view)
        if request.method == "POST" and shared.permission_form.validate():
            permission_name = shared.permission_form.permission.data
            self.base_view.permission_post(shared.group, permission_name)
            url = request.route_url('admin_object', object='groups',
                                    object_id=shared.group.id, verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=url)

        return {'group': shared.group,
                'group_form': shared.group_form,
                'permission_form': shared.permission_form,
                'permissions_grid': shared.permissions_grid}

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'relation=permissions',
                     'verb=DELETE'),
        request_method="GET")
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=groups', 'relation=permissions',
                     'verb=DELETE'),
        request_method="POST")
    def permission_delete(self):
        request = self.request
        group = self.base_view.group_get(request.matchdict['object_id'])
        permission = self.base_view.permission_get(
            group, request.GET.get('permission'))
        back_url = request.route_url(
            'admin_object', object='groups', object_id=group.id,
            verb='GET')

        if request.method == "POST":
            self.base_view.permission_delete(group, permission)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {"parent_obj": group,
                "member_obj": permission,
                "confirm_url": request.current_route_url(),
                "back_url": back_url
                }
