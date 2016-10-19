# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.models.services.group import GroupService

from marshmallow import (Schema, fields, validate, validates, pre_load)

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
    parent_id = fields.Int(dump_only=True)
    resource_type = fields.Str(dump_only=True)
    resource_name = fields.Str(required=True, validate=(validate.Length(100)))
    ordering = fields.Int()
    owner_user_id = fields.Int()
    owner_group_id = fields.Int()


class EntryCreateSchema(ResourceCreateSchemaMixin):
    class Meta(object):
        strict = True
        ordered = True

    note = fields.Str()
