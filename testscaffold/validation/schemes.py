# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.models.services.group import GroupService

from marshmallow import (Schema, fields, validate, validates, pre_load)


class UserRegisterSchema(Schema):
    class Meta(object):
        strict = True
        ordered = True

    user_name = fields.Str(required=True, validate=(validate.Length(3)))
    password = fields.Str(required=True, validate=(validate.Length(3)))
    email = fields.Str(required=True, validate=(validate.Email()))

    @validates('user_name')
    def validate_user_name(self, value):
        request = self.context['request']
        modified_obj = self.context.get('modified_obj')
        user = UserService.by_user_name(value, db_session=request.dbsession)
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


class UserEditSchema(UserRegisterSchema):
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

    group_name = fields.Str()
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
