# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory

from ziggurat_foundations.models.services.resource import ResourceService
from ziggurat_foundations.models.services.user_resource_permission import \
    UserResourcePermissionService
from ziggurat_foundations.models.services.group_resource_permission import \
    GroupResourcePermissionService

from testscaffold.util import safe_integer
from testscaffold.models.user_resource_permission import UserResourcePermission
from testscaffold.models.group_resource_permission import GroupResourcePermission

ENTRIES_PER_PAGE = 50

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


class ResourcesShared(object):
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate
        self.page = 1

    def resource_get(self, resource_id):
        request = self.request
        resource = ResourceService.get(safe_integer(resource_id),
                                       db_session=request.dbsession)
        if not resource:
            raise pyramid.httpexceptions.HTTPNotFound()
        return resource

    def user_permission_post(self, resource, user_id, permission):
        perm_inst = UserResourcePermission(
            user_id=user_id,
            perm_name=permission
        )
        resource.user_permissions.append(perm_inst)
        return perm_inst

    def user_permission_delete(self, resource, user_id, perm_name):
        perm_inst = UserResourcePermissionService.get(
            resource_id=resource.resource_id, user_id=user_id,
            perm_name=perm_name, db_session=self.request.dbsession)
        resource.user_permissions.remove(perm_inst)
        return True

    def group_permission_post(self, resource, group_id, permission):
        perm_inst = GroupResourcePermission(
            group_id=group_id,
            perm_name=permission
        )
        resource.group_permissions.append(perm_inst)
        return perm_inst

    def group_permission_delete(self, resource, group_id, perm_name):
        perm_inst = GroupResourcePermissionService.get(
            resource_id=resource.resource_id, group_id=group_id,
            perm_name=perm_name, db_session=self.request.dbsession)
        resource.group_permissions.remove(perm_inst)
        return True