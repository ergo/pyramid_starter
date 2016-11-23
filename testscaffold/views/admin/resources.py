# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import pyramid.httpexceptions as httpexceptions

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults
from ziggurat_foundations.models.services.user import UserService

from testscaffold.validation.schemes import (UserResourcePermissionSchema,
                                             GroupResourcePermissionSchema)

from testscaffold.views.shared.users import UsersShared
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


@view_defaults(route_name='admin_object_relation', permission='admin_users')
class AdminResourceRelationsView(BaseView):
    """
    Handles operations on group properties
    """

    def __init__(self, request):
        super(AdminResourceRelationsView, self).__init__(request)
        self.shared = UsersShared(request)

    @view_config(renderer='testscaffold:templates/admin/users/edit.jinja2',
                 match_param=['object=resources', 'relation=user_permissions',
                              'verb=POST'])
    def permission_post(self):
        request = self.request
        resource = self.request.context.resource
        came_from = request.headers.get('Referer')
        user = self.shared.user_get(request.matchdict['object_id'])

        schema = UserResourcePermissionSchema(
            context={'request': self.request,
                     'resource': resource})
        data = {
            'user_name': self.request.POST.get('user_name'),
            'perm_name': self.request.POST.get('perm_name')
        }
        data = schema.load(data).data
        user = UserService.by_user_name(
            data['user_name'], db_session=self.request.dbsession)

        perm_inst = self.shared.user_permission_post(
            resource, user.id, data['perm_name'])
        location = came_from or request.route_url('admin')
        return httpexceptions.HTTPFound(location=location)

    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=resources', 'relation=user_permissions',
                     'verb=DELETE'),
        request_method="GET")
    @view_config(
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=resources', 'relation=user_permissions',
                     'verb=DELETE'),
        request_method="POST")
    def permission_delete(self):
        request = self.request
        user = self.shared.user_get(request.matchdict['object_id'])
        permission = self.shared.permission_get(
            user, request.GET.get('permission'))
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
