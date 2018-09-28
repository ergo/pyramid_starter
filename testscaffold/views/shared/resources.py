# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory
from testscaffold.services.group_resource_permission import (
    GroupResourcePermissionService,
)
from testscaffold.services.user_resource_permission import UserResourcePermissionService

from testscaffold.models.group_resource_permission import GroupResourcePermission
from testscaffold.models.user_resource_permission import UserResourcePermission
from testscaffold.util import safe_integer

ENTRIES_PER_PAGE = 50

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


class ResourcesShared(object):
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate
        self.page = 1

    def user_permission_post(self, resource, user_id, perm_name):
        perm_inst = UserResourcePermission(user_id=user_id, perm_name=perm_name)
        resource.user_permissions.append(perm_inst)
        return perm_inst

    def user_permission_get(self, resource_id, user_id, perm_name):
        perm_inst = UserResourcePermissionService.get(
            resource_id=resource_id,
            user_id=user_id,
            perm_name=perm_name,
            db_session=self.request.dbsession,
        )
        if not perm_inst:
            raise pyramid.httpexceptions.HTTPNotFound()
        return perm_inst

    def group_permission_get(self, resource_id, group_id, perm_name):
        perm_inst = GroupResourcePermissionService.get(
            resource_id=resource_id,
            group_id=group_id,
            perm_name=perm_name,
            db_session=self.request.dbsession,
        )
        if not perm_inst:
            raise pyramid.httpexceptions.HTTPNotFound()
        return perm_inst

    def user_permission_delete(self, resource, user_id, perm_name):
        perm_inst = self.user_permission_get(resource.resource_id, user_id, perm_name)
        resource.user_permissions.remove(perm_inst)
        return True

    def group_permission_post(self, resource, group_id, permission):
        perm_inst = GroupResourcePermission(group_id=group_id, perm_name=permission)
        resource.group_permissions.append(perm_inst)
        return perm_inst

    def group_permission_delete(self, resource, group_id, perm_name):
        perm_inst = GroupResourcePermissionService.get(
            resource_id=resource.resource_id,
            group_id=group_id,
            perm_name=perm_name,
            db_session=self.request.dbsession,
        )
        resource.group_permissions.remove(perm_inst)
        return True
