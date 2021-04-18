import logging

import pyramid.httpexceptions as httpexceptions
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.services.group import GroupService
from testscaffold.services.user import UserService
from testscaffold.validation.schemes import (
    UserResourcePermissionSchema,
    GroupResourcePermissionSchema,
)
from testscaffold.views import BaseView
from testscaffold.views.shared.resources import ResourcesShared

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


@view_defaults(route_name="admin_object_relation", permission="admin_users")
class AdminResourceRelationsView(BaseView):
    """
    Handles operations on group properties
    """

    def __init__(self, request):
        super(AdminResourceRelationsView, self).__init__(request)
        self.shared = ResourcesShared(request)

    @view_config(
        renderer="testscaffold:templates/admin/users/edit.jinja2",
        match_param=["object=resources", "relation=user_permissions", "verb=POST"],
    )
    def user_permission_post(self):
        request = self.request
        resource = self.request.context.resource
        came_from = request.headers.get("Referer")
        schema = UserResourcePermissionSchema(
            context={"request": self.request, "resource": resource}
        )
        data = {
            "user_name": self.request.POST.get("user_name"),
            "perm_name": self.request.POST.get("perm_name"),
        }
        data = schema.load(data)
        user = UserService.by_user_name(
            data["user_name"], db_session=self.request.dbsession
        )

        perm_inst = self.shared.user_permission_post(
            resource, user.id, data["perm_name"]
        )
        location = came_from or request.route_url("admin")
        return httpexceptions.HTTPFound(location=location)

    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=resources", "relation=user_permissions", "verb=DELETE"),
        request_method="GET",
    )
    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=resources", "relation=user_permissions", "verb=DELETE"),
        request_method="POST",
    )
    def user_permission_delete(self):
        request = self.request
        resource = self.request.context.resource
        user = UserService.by_user_name(
            request.GET.get("user_name"), db_session=self.request.dbsession
        )
        permission = self.shared.user_permission_get(
            resource.resource_id, user.id, request.GET.get("perm_name")
        )

        back_url = request.route_url(
            "admin_object",
            object=resource.plural_type,
            object_id=resource.resource_id,
            verb="GET",
        )

        if request.method == "POST":
            self.shared.user_permission_delete(
                resource, user.id, request.GET.get("perm_name")
            )
            return httpexceptions.HTTPFound(location=back_url)

        return {
            "parent_obj": user,
            "member_obj": permission,
            "confirm_url": request.current_route_url(),
            "back_url": back_url,
        }

    @view_config(
        renderer="testscaffold:templates/admin/groups/edit.jinja2",
        match_param=["object=resources", "relation=group_permissions", "verb=POST"],
    )
    def group_permission_post(self):
        request = self.request
        resource = self.request.context.resource
        came_from = request.headers.get("Referer")
        schema = GroupResourcePermissionSchema(
            context={"request": self.request, "resource": resource}
        )
        data = {
            "group_id": self.request.POST.get("group_id"),
            "perm_name": self.request.POST.get("perm_name"),
        }
        data = schema.load(data)
        group = GroupService.get(data["group_id"], db_session=self.request.dbsession)

        perm_inst = self.shared.group_permission_post(
            resource, group.id, data["perm_name"]
        )
        location = came_from or request.route_url("admin")
        return httpexceptions.HTTPFound(location=location)

    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=resources", "relation=group_permissions", "verb=DELETE"),
        request_method="GET",
    )
    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=resources", "relation=group_permissions", "verb=DELETE"),
        request_method="POST",
    )
    def group_permission_delete(self):
        request = self.request
        resource = self.request.context.resource
        group = GroupService.get(
            request.GET.get("group_id"), db_session=self.request.dbsession
        )
        permission = self.shared.group_permission_get(
            resource.resource_id, group.id, request.GET.get("perm_name")
        )

        back_url = request.route_url(
            "admin_object",
            object=resource.plural_type,
            object_id=resource.resource_id,
            verb="GET",
        )

        if request.method == "POST":
            self.shared.group_permission_delete(
                resource, group.id, request.GET.get("perm_name")
            )
            return httpexceptions.HTTPFound(location=back_url)

        return {
            "parent_obj": group,
            "member_obj": permission,
            "confirm_url": request.current_route_url(),
            "back_url": back_url,
        }
