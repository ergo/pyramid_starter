# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.grids import UsersGrid, UserPermissionsGrid
from testscaffold.models.user import User
from testscaffold.util import safe_integer
from testscaffold.validation.forms import (
    UserAdminCreateForm,
    UserAdminUpdateForm,
    DirectPermissionForm)
from testscaffold.views import BaseView
from testscaffold.views.shared.users import UsersShared, USERS_PER_PAGE

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


@view_defaults(route_name='admin_objects', permission='admin_users')
class AdminUsersViews(BaseView):
    def __init__(self, request):
        super(AdminUsersViews, self).__init__(request)
        self.shared = UsersShared(request)

    @view_config(renderer='testscaffold:templates/admin/users/index.jinja2',
                 match_param=('object=users', 'verb=GET'))
    def collection_list(self):
        page = safe_integer(self.request.GET.get('page', 1))
        user_paginator = self.shared.collection_list(page=page)
        start_number = (USERS_PER_PAGE * (self.shared.page - 1) + 1) or 1
        user_grid = UsersGrid(user_paginator,
                              start_number=start_number, request=self.request)

        return {'user_paginator': user_paginator,
                'user_grid': user_grid}

    @view_config(renderer='testscaffold:templates/admin/users/edit.jinja2',
                 match_param=('object=users', 'verb=POST'))
    def post(self):
        request = self.request
        user_form = UserAdminCreateForm(
            request.POST, context={'request': request})
        if request.method == "POST" and user_form.validate():
            user = User()
            self.shared.populate_instance(user, user_form.data)
            user.persist(flush=True, db_session=request.dbsession)
            log.info('users_post', extra={'user_id': user.id,
                                          'user_name': user.user_name})
            request.session.flash(
                {'msg': self.translate(_('User created.')), 'level': 'success'})
            location = request.route_url('admin_objects', object='users',
                                         verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=location)

        return {"user_form": user_form}


@view_defaults(route_name='admin_object', permission='admin_users')
class AdminUserViews(BaseView):
    def __init__(self, request):
        super(AdminUserViews, self).__init__(request)
        self.shared = UsersShared(request)

    @view_config(renderer='testscaffold:templates/admin/users/edit.jinja2',
                 match_param=('object=users', 'verb=GET'))
    @view_config(renderer='testscaffold:templates/admin/users/edit.jinja2',
                 match_param=('object=users', 'verb=PATCH'))
    def get_patch(self):
        request = self.request
        user = self.shared.user_get(self.request.matchdict['object_id'])
        permission_form = DirectPermissionForm(
            request.POST, context={'request': request})
        permissions_grid = UserPermissionsGrid(
            user.user_permissions, request=request, user=user)

        user_form = UserAdminUpdateForm(
            request.POST, obj=user, context={'request': request,
                                             'modified_obj': user})

        if request.method == "POST" and user_form.validate():
            self.shared.populate_instance(user, user_form.data)

        return {"user": user,
                "user_form": user_form,
                "permission_form": permission_form,
                "permissions_grid": permissions_grid}

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=users', 'verb=DELETE'),
        request_method='GET')
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=users', 'verb=DELETE'),
        request_method='POST')
    def delete(self):
        request = self.request
        user = self.shared.user_get(self.request.matchdict['object_id'])
        back_url = request.route_url('admin_objects', object='users',
                                     verb='GET')

        if request.method == "POST":
            self.shared.delete(user)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {"parent_obj": user,
                "member_obj": None,
                "confirm_url": request.current_route_url(),
                "back_url": back_url
                }


@view_defaults(route_name='admin_object_relation', permission='admin_users')
class AdminUserRelationsView(BaseView):
    """
    Handles operations on group properties
    """

    def __init__(self, request):
        super(AdminUserRelationsView, self).__init__(request)
        self.shared = UsersShared(request)

    @view_config(renderer='testscaffold:templates/admin/users/edit.jinja2',
                 match_param=['object=users', 'relation=permissions',
                              'verb=POST'])
    def permission_post(self):
        request = self.request
        user = self.shared.user_get(request.matchdict['object_id'])
        user_form = UserAdminUpdateForm(
            request.POST, obj=user,
            context={'request': request, 'modified_obj': user}
        )
        permission_form = DirectPermissionForm(
            request.POST, context={'request': request})
        permissions_grid = UserPermissionsGrid(
            user.permissions, request=request, user=user)

        if request.method == "POST" and permission_form.validate():
            permission_name = permission_form.perm_name.data
            self.shared.permission_post(user, permission_name)
            url = request.route_url('admin_object', object='users',
                                    object_id=user.id, verb='GET')
            return pyramid.httpexceptions.HTTPFound(location=url)

        return {'user': user,
                'user_form': user_form,
                'permission_form': permission_form,
                'permissions_grid': permissions_grid}

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=users', 'relation=permissions',
                     'verb=DELETE'),
        request_method="GET")
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=users', 'relation=permissions',
                     'verb=DELETE'),
        request_method="POST")
    def permission_delete(self):
        request = self.request
        user = self.shared.user_get(request.matchdict['object_id'])
        permission = self.shared.permission_get(
            user, request.GET.get('perm_name'))
        back_url = request.route_url(
            'admin_object', object='users', object_id=user.id,
            verb='GET')

        if request.method == "POST":
            self.shared.permission_delete(user, permission)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {"parent_obj": user,
                "member_obj": permission,
                "confirm_url": request.current_route_url(),
                "back_url": back_url
                }
