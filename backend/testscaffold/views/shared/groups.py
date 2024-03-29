from __future__ import absolute_import

import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory

from testscaffold.models.db import Group
from testscaffold.models.db import GroupPermission
from testscaffold.services.group import GroupService
from testscaffold.services.group_permission import GroupPermissionService
from testscaffold.services.user import UserService

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


class GroupsShared:
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.translate = request.localizer.translate

    def collection_list(self):
        groups = GroupService.all(Group, db_session=self.request.dbsession)
        return groups

    def group_get(self, obj_id):
        request = self.request
        group = GroupService.get(obj_id, db_session=request.dbsession)
        if not group:
            raise pyramid.httpexceptions.HTTPNotFound()
        return group

    def user_get(self, obj_id):
        request = self.request
        user = UserService.get(obj_id, db_session=request.dbsession)
        if not user:
            raise pyramid.httpexceptions.HTTPNotFound()
        return user

    def user_get_by_username(self, user_name):
        request = self.request
        user = UserService.by_user_name(user_name, db_session=request.dbsession)
        if not user:
            raise pyramid.httpexceptions.HTTPNotFound()
        return user

    def permission_get(self, group, permission):
        permission = GroupPermissionService.by_group_and_perm(group.id, permission, db_session=self.request.dbsession)
        if not permission:
            raise pyramid.httpexceptions.HTTPNotFound()
        return permission

    def populate_instance(self, instance, data, *args, **kwargs):
        instance.populate_obj(data, *args, **kwargs)
        log.info("group_populate_instance", extra={"action": "updated"})

    def delete(self, instance):
        log.info(
            "group_delete", extra={"group_id": instance.id, "group_name": instance.group_name},
        )
        instance.delete(self.request.dbsession)
        self.request.session.flash({"msg": self.translate(_("Group removed.")), "level": "success"})

    def permission_post(self, group, perm_name):
        try:
            permission_inst = self.permission_get(group, perm_name)
        except pyramid.httpexceptions.HTTPNotFound:
            log.info(
                "group_permission_post",
                extra={"group_id": group.id, "group_name": group.group_name, "perm_name": perm_name,},
            )
            permission_inst = GroupPermission(perm_name=perm_name)
            group.permissions.append(permission_inst)
            self.request.session.flash(
                {"msg": self.translate(_("Permission granted for group.")), "level": "success",}
            )
        return permission_inst

    def permission_delete(self, group, permission):
        permission_inst = GroupPermissionService.by_group_and_perm(
            group.id, permission.perm_name, db_session=self.request.dbsession
        )
        if permission_inst:
            log.info(
                "group_permission_delete",
                extra={"group_id": group.id, "group_name": group.group_name, "perm_name": permission.perm_name,},
            )
            group.permissions.remove(permission_inst)
            self.request.session.flash(
                {"msg": self.translate(_("Permission withdrawn from group.")), "level": "success",}
            )

    def user_post(self, group, user):
        if user not in group.users:
            group.users.append(user)
            self.request.session.flash({"msg": self.translate(_("User added to group.")), "level": "success"})
            log.info(
                "group_user_post",
                extra={
                    "group_id": group.id,
                    "user": user.id,
                    "group_name": group.group_name,
                    "user_name": user.user_name,
                },
            )

    def user_delete(self, group, user):
        if user in group.users:
            group.users.remove(user)
            self.request.session.flash(
                {"msg": self.translate(_("User removed from group.")), "level": "success",}
            )
            log.info(
                "group_user_delete",
                extra={
                    "group_id": group.id,
                    "user_id": user.id,
                    "group_name": group.group_name,
                    "user_name": user.user_name,
                },
            )
