# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.models.services.group import GroupService
from ziggurat_foundations.models.services.resource import ResourceService
from ziggurat_foundations.models.services.resource import (
    ZigguratResourceOutOfBoundaryException,
    ZigguratResourceTreeMissingException,
    ZigguratResourceTreePathException, noop)

from marshmallow import (Schema, fields, validate, validates, pre_load,
                         validates_schema)

user_regex_error = 'Username can only consist of ' \
                   'alphanumerical characters, hypens and underscores'


class UserCreateSchema(Schema):
    class Meta(object):
        strict = True
        ordered = True

    id = fields.Int(dump_only=True)
    user_name = fields.Str(required=True,
                           validate=(validate.Length(3),
                                     validate.Regexp('^[\w-]*$',
                                                     error=user_regex_error)))
    password = fields.Str(required=True, validate=(validate.Length(3)))
    email = fields.Str(required=True, validate=(validate.Email()))
    status = fields.Int(dump_only=True)
    last_login_date = fields.DateTime(dump_only=True)
    registered_date = fields.DateTime(dump_only=True)

    @validates('user_name')
    def validate_user_name(self, value):
        request = self.context['request']
        modified_obj = self.context.get('modified_obj')
        user = UserService.by_user_name(value, db_session=request.dbsession)
        by_admin = request.has_permission('root_administrator')
        if modified_obj and not by_admin:
            msg = 'Only administrator can change usernames'
            raise validate.ValidationError(msg)
        if user:
            if not modified_obj or modified_obj.id != user.id:
                msg = 'User already exists in database'
                raise validate.ValidationError(msg)

    @validates('email')
    def validate_email(self, value):
        request = self.context['request']
        modified_obj = self.context.get('modified_obj')
        user = UserService.by_email(value, db_session=request.dbsession)
        if user:
            if not modified_obj or modified_obj.id != user.id:
                msg = 'Email already exists in database'
                raise validate.ValidationError(msg)


class UserEditSchema(UserCreateSchema):
    password = fields.Str(required=False, validate=(validate.Length(3)))


class UserSearchSchema(Schema):
    class Meta(object):
        strict = True
        ordered = True

    user_name = fields.Str()
    user_name_like = fields.Str()

    # @pre_load()
    # def make_object(self, data):
    #     return list(data)


class GroupEditSchema(Schema):
    class Meta(object):
        strict = True
        ordered = True

    id = fields.Int(dump_only=True)
    member_count = fields.Int(dump_only=True)
    group_name = fields.Str(required=True,
                            validate=(validate.Length(3)))
    description = fields.Str()

    @validates('group_name')
    def validate_group_name(self, value):
        request = self.context['request']
        modified_obj = self.context.get('modified_obj')
        group = GroupService.by_group_name(value, db_session=request.dbsession)
        if group:
            if not modified_obj or modified_obj.id != group.id:
                msg = 'Group already exists in database'
                raise validate.ValidationError(msg)


class ResourceCreateSchemaMixin(Schema):
    class Meta(object):
        strict = True
        ordered = True

    resource_id = fields.Int(dump_only=True)
    resource_type = fields.Str(dump_only=True)
    parent_id = fields.Int()
    resource_name = fields.Str(required=True, validate=(validate.Length(
        min=1, max=100)))
    ordering = fields.Int()
    owner_user_id = fields.Int(dump_only=True)
    owner_group_id = fields.Int(dump_only=True)

    @pre_load()
    def populate_ordering(self, data):
        request = self.context['request']
        if not data.get('ordering'):
            data['ordering'] = ResourceService.count_children(
                None, db_session=request.dbsession) + 1

    @validates('parent_id')
    def validate_parent_id(self, value):
        request = self.context['request']
        resource = self.context.get('modified_obj')
        new_parent_id = value
        if not new_parent_id:
            return True

        resource_id = resource.resource_id if resource else None
        if resource_id is None:
            return True

        try:
            ResourceService.check_node_parent(
                resource_id, new_parent_id, db_session=request.dbsession)
        except ZigguratResourceTreeMissingException:
            msg = 'New parent node not found'
            raise validate.ValidationError(msg)
        except ZigguratResourceTreePathException:
            msg = 'Trying to insert node into itself'
            raise validate.ValidationError(msg)

    @validates_schema
    def validate_ordering(self, data):
        request = self.context['request']
        resource = self.context.get('modified_obj')
        new_parent_id = data.get('parent_id') or noop
        to_position = data.get('ordering')
        if not to_position or to_position == 1:
            return

        same_branch = False

        # reset if parent is same as old
        if resource and new_parent_id == resource.parent_id:
            new_parent_id = noop

        if new_parent_id is noop:
            same_branch = True

        if resource:
            parent_id = resource.parent_id if new_parent_id is noop else new_parent_id
        else:
            parent_id = new_parent_id if new_parent_id is not noop else None
        try:
            ResourceService.check_node_position(
                parent_id, to_position, on_same_branch=same_branch,
                db_session=request.dbsession)
        except ZigguratResourceOutOfBoundaryException:
            msg = 'Too small or too big parent_id'
            raise validate.ValidationError(msg)


class EntryCreateSchemaAdmin(ResourceCreateSchemaMixin):
    class Meta(object):
        strict = True
        ordered = True

    note = fields.Str()
    owner_user_id = fields.Int()
    owner_group_id = fields.Int()
