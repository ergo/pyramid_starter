import logging

import pyramid.httpexceptions
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults

from testscaffold.grids import GroupsGrid, UsersGroupsGrid, GroupPermissionsGrid
from testscaffold.models.group import Group
from testscaffold.services.group import GroupService
from testscaffold.util import safe_integer
from testscaffold.validation.forms import GroupUpdateForm, DirectPermissionForm
from testscaffold.views import BaseView
from testscaffold.views.api.groups import GROUPS_PER_PAGE
from testscaffold.views.shared.groups import GroupsShared

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


@view_defaults(route_name="admin_objects", permission="admin_groups")
class AdminGroupsView(BaseView):
    """
    Handles group list and new group form
    """

    def __init__(self, request):
        super(AdminGroupsView, self).__init__(request)
        self.shared = GroupsShared(request)

    @view_config(
        renderer="testscaffold:templates/admin/groups/index.jinja2",
        match_param=("object=groups", "verb=GET"),
    )
    def collection_list(self):
        groups = self.shared.collection_list()
        groups_grid = GroupsGrid(groups, request=self.request)
        return {"groups": groups, "groups_grid": groups_grid}

    @view_config(
        renderer="testscaffold:templates/admin/groups/edit.jinja2",
        match_param=("object=groups", "verb=POST"),
    )
    def groups_post(self):
        request = self.request
        group = Group()
        group_form = GroupUpdateForm(request.POST, context={"request": request})

        if request.method == "POST" and group_form.validate():
            self.shared.populate_instance(group, group_form.data)
            group.persist(flush=True, db_session=request.dbsession)
            log.info(
                "groups_post",
                extra={"group_id": group.id, "group_name": group.group_name},
            )
            request.session.flash(
                {"msg": self.translate(_("Group created.")), "level": "success"}
            )
            location = request.route_url("admin_objects", object="groups", verb="GET")
            return pyramid.httpexceptions.HTTPFound(location=location)

        return {"group": group, "group_form": group_form}


@view_defaults(route_name="admin_object", permission="admin_groups")
class AdminGroupView:
    """
    Handles operations on individual group
    """

    def __init__(self, request):
        self.request = request
        self.shared = GroupsShared(request)

    @view_config(
        renderer="testscaffold:templates/admin/groups/edit.jinja2",
        match_param=("object=groups", "verb=GET"),
    )
    @view_config(
        renderer="testscaffold:templates/admin/groups/edit.jinja2",
        match_param=("object=groups", "verb=PATCH"),
    )
    def group_get_patch(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        group_form = GroupUpdateForm(
            request.POST, obj=group, context={"request": request, "modified_obj": group}
        )
        permission_form = DirectPermissionForm(
            request.POST, context={"request": request}
        )
        permissions_grid = GroupPermissionsGrid(
            group.permissions, request=request, group=group
        )
        if request.method == "POST" and group_form.validate():
            self.shared.populate_instance(group, group_form.data)
            request.session.flash({"msg": _("Group updated."), "level": "success"})
            url = request.route_url(
                "admin_object", object="groups", object_id=group.id, verb="GET"
            )
            return pyramid.httpexceptions.HTTPFound(location=url)

        return {
            "group": group,
            "group_form": group_form,
            "permission_form": permission_form,
            "permissions_grid": permissions_grid,
        }

    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "verb=DELETE"),
        request_method="GET",
    )
    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "verb=DELETE"),
        request_method="POST",
    )
    def group_delete(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        back_url = request.route_url("admin_objects", object="groups", verb="GET")

        if request.method == "POST":
            self.shared.delete(group)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {
            "parent_obj": group,
            "member_obj": None,
            "confirm_url": request.current_route_url(),
            "back_url": back_url,
        }


@view_defaults(route_name="admin_object_relation", permission="admin_groups")
class AdminGroupRelationsView:
    """
    Handles operations on group properties
    """

    def __init__(self, request):
        self.request = request
        self.shared = GroupsShared(request)

    @view_config(
        renderer="testscaffold:templates/admin/groups/users_list.jinja2",
        match_param=["object=groups", "relation=users", "verb=GET"],
    )
    def users_get(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        page = safe_integer(request.GET.get("page", 1))

        user_paginator = GroupService.get_user_paginator(
            group,
            page=page,
            items_per_page=GROUPS_PER_PAGE,
            url_maker=lambda p: request.current_route_url(_query={"page": p}),
            db_session=request.dbsession,
        )

        user_grid = UsersGroupsGrid(
            user_paginator,
            columns=["_numbered", "user_name", "email", "registered_date", "options"],
            start_number=GROUPS_PER_PAGE * (page - 1) or 1,
            request=request,
            group=group,
        )
        return {"group": group, "user_grid": user_grid}

    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "relation=users", "verb=DELETE"),
        request_method="GET",
    )
    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "relation=users", "verb=DELETE"),
        request_method="POST",
    )
    def user_delete(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        user = self.shared.user_get(request.GET.get("user_id"))
        back_url = request.route_url(
            "admin_object_relation",
            object="groups",
            object_id=group.id,
            relation="users",
            verb="GET",
        )

        if request.method == "POST":
            self.shared.user_delete(group, user)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {
            "parent_obj": group,
            "member_obj": user,
            "confirm_url": request.current_route_url(),
            "back_url": back_url,
        }

    @view_config(
        renderer="testscaffold:templates/admin/groups/edit.jinja2",
        match_param=["object=groups", "relation=permissions", "verb=POST"],
    )
    def permission_post(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        group_form = GroupUpdateForm(
            request.POST, obj=group, context={"request": request, "modified_obj": group}
        )
        permission_form = DirectPermissionForm(
            request.POST, context={"request": request}
        )
        permissions_grid = GroupPermissionsGrid(
            group.permissions, request=request, group=group
        )

        if request.method == "POST" and permission_form.validate():
            permission_name = permission_form.perm_name.data
            self.shared.permission_post(group, permission_name)
            url = request.route_url(
                "admin_object", object="groups", object_id=group.id, verb="GET"
            )
            return pyramid.httpexceptions.HTTPFound(location=url)

        return {
            "group": group,
            "group_form": group_form,
            "permission_form": permission_form,
            "permissions_grid": permissions_grid,
        }

    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "relation=permissions", "verb=DELETE"),
        request_method="GET",
    )
    @view_config(
        renderer="testscaffold:templates/admin/relation_remove.jinja2",
        match_param=("object=groups", "relation=permissions", "verb=DELETE"),
        request_method="POST",
    )
    def permission_delete(self):
        request = self.request
        group = self.shared.group_get(request.matchdict["object_id"])
        permission = self.shared.permission_get(group, request.GET.get("perm_name"))
        back_url = request.route_url(
            "admin_object", object="groups", object_id=group.id, verb="GET"
        )

        if request.method == "POST":
            self.shared.permission_delete(group, permission)
            return pyramid.httpexceptions.HTTPFound(location=back_url)

        return {
            "parent_obj": group,
            "member_obj": permission,
            "confirm_url": request.current_route_url(),
            "back_url": back_url,
        }
