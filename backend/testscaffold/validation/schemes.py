from marshmallow import Schema, fields, validate, validates, validates_schema, EXCLUDE
from pyramid.i18n import TranslationStringFactory
from ziggurat_foundations import noop
from ziggurat_foundations.exc import (
    ZigguratResourceOutOfBoundaryException,
    ZigguratResourceTreeMissingException,
    ZigguratResourceTreePathException,
)

from testscaffold.services.group import GroupService
from testscaffold.services.resource_tree_service import tree_service
from testscaffold.services.user import UserService

_ = TranslationStringFactory("testscaffold")

user_regex_error = _(
    "Username can only consist of " "alphanumerical characters, hypens and underscores"
)


class BaseTestScaffoldSchema(Schema):
    class Meta:
        strict = True
        ordered = True
        unknown = EXCLUDE


class UserCreateSchema(BaseTestScaffoldSchema):

    id = fields.Int(dump_only=True)
    user_name = fields.Str(
        required=True,
        validate=(
            validate.Length(3),
            validate.Regexp("^[\w-]*$", error=user_regex_error),
        ),
    )
    password = fields.Str(required=True, validate=(validate.Length(3)))
    email = fields.Str(
        required=True, validate=(validate.Email(error=_("Not a valid email")))
    )
    status = fields.Int(dump_only=True)
    last_login_date = fields.DateTime(dump_only=True)
    registered_date = fields.DateTime(dump_only=True)

    @validates("user_name")
    def validate_user_name(self, value):
        request = self.context["request"]
        modified_obj = self.context.get("modified_obj")
        user = UserService.by_user_name(value, db_session=request.dbsession)
        by_admin = request.has_permission("root_administration")
        if modified_obj and not by_admin and (modified_obj.user_name != value):
            msg = _("Only administrator can change usernames")
            raise validate.ValidationError(msg)
        if user:
            if not modified_obj or modified_obj.id != user.id:
                msg = _("User already exists in database")
                raise validate.ValidationError(msg)

    @validates("email")
    def validate_email(self, value):
        request = self.context["request"]
        modified_obj = self.context.get("modified_obj")
        user = UserService.by_email(value, db_session=request.dbsession)
        if user:
            if not modified_obj or modified_obj.id != user.id:
                msg = _("Email already exists in database")
                raise validate.ValidationError(msg)


class UserEditSchema(UserCreateSchema):
    password = fields.Str(required=False, validate=(validate.Length(3)))


class UserSearchSchema(BaseTestScaffoldSchema):

    user_name = fields.Str()
    user_name_like = fields.Str()

    # @pre_load()
    # def make_object(self, data):
    #     return list(data)


class GroupEditSchema(BaseTestScaffoldSchema):

    id = fields.Int(dump_only=True)
    member_count = fields.Int(dump_only=True)
    group_name = fields.Str(required=True, validate=(validate.Length(3)))
    description = fields.Str()

    @validates("group_name")
    def validate_group_name(self, value):
        request = self.context["request"]
        modified_obj = self.context.get("modified_obj")
        group = GroupService.by_group_name(value, db_session=request.dbsession)
        if group:
            if not modified_obj or modified_obj.id != group.id:
                msg = _("Group already exists in database")
                raise validate.ValidationError(msg)


class ResourceCreateSchemaMixin(BaseTestScaffoldSchema):

    resource_id = fields.Int(dump_only=True)
    resource_type = fields.Str(dump_only=True)
    parent_id = fields.Int()
    resource_name = fields.Str(
        required=True, validate=(validate.Length(min=1, max=100))
    )
    ordering = fields.Int()
    owner_user_id = fields.Int(dump_only=True)
    owner_group_id = fields.Int(dump_only=True)

    @validates("parent_id")
    def validate_parent_id(self, value):
        request = self.context["request"]
        resource = self.context.get("modified_obj")
        new_parent_id = value
        if not new_parent_id:
            return True
        resource_id = resource.resource_id if resource else None
        if new_parent_id is None:
            return True

        try:
            tree_service.check_node_parent(
                resource_id, new_parent_id, db_session=request.dbsession
            )
        except ZigguratResourceTreeMissingException as exc:
            raise validate.ValidationError(str(exc))
        except ZigguratResourceTreePathException as exc:
            raise validate.ValidationError(str(exc))

    @validates_schema
    def validate_ordering(self, data, **kwargs):
        request = self.context["request"]
        resource = self.context.get("modified_obj")
        new_parent_id = data.get("parent_id") or noop
        to_position = data.get("ordering")
        if to_position is None or to_position == 1:
            return

        same_branch = False

        # reset if parent is same as old
        if resource and new_parent_id == resource.parent_id:
            new_parent_id = noop

        if new_parent_id is noop and resource:
            same_branch = True

        if resource:
            parent_id = resource.parent_id if new_parent_id is noop else new_parent_id
        else:
            parent_id = new_parent_id if new_parent_id is not noop else None
        try:
            tree_service.check_node_position(
                parent_id,
                to_position,
                on_same_branch=same_branch,
                db_session=request.dbsession,
            )
        except ZigguratResourceOutOfBoundaryException as exc:
            raise validate.ValidationError(str(exc), "ordering")


class EntryCreateSchema(ResourceCreateSchemaMixin):
    note = fields.Str()


class EntryCreateSchemaAdmin(ResourceCreateSchemaMixin):

    note = fields.Str()
    owner_user_id = fields.Int()
    owner_group_id = fields.Int()


class UserResourcePermissionSchema(BaseTestScaffoldSchema):

    user_name = fields.Str(required=True)

    perm_name = fields.Str(required=True)

    @validates("user_name")
    def validate_user_name(self, value):
        request = self.context["request"]
        user = UserService.by_user_name(value, db_session=request.dbsession)
        if not user:
            raise validate.ValidationError(_("User not found"))

    @validates("perm_name")
    def validate_perm_name(self, value):
        perms = self.context["resource"].__possible_permissions__
        if value not in perms:
            raise validate.ValidationError(_("Incorrect permission name for resource"))


class GroupResourcePermissionSchema(BaseTestScaffoldSchema):

    group_id = fields.Int(required=True)

    perm_name = fields.Str(required=True)

    @validates("group_id")
    def validate_group_id(self, value):
        request = self.context["request"]
        group = GroupService.get(value, db_session=request.dbsession)
        if not group:
            raise validate.ValidationError(_("Group not found"))

    @validates("perm_name")
    def validate_perm_name(self, value):
        perms = self.context["resource"].__possible_permissions__
        if value not in perms:
            raise validate.ValidationError(_("Incorrect permission name for resource"))
