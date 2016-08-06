# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from datetime import datetime

import pyramid.httpexceptions

from pyramid.view import view_config, view_defaults

from testscaffold.util import safe_integer
from testscaffold.models.user import User
from testscaffold.services.user import UserService
from testscaffold.validation.schemes import UserSearchSchema
from testscaffold.validation.schemes import UserCreateSchema
from testscaffold.validation.schemes import UserEditSchema

log = logging.getLogger(__name__)

USERS_PER_PAGE = 50


class UsersViewBase(object):
    """
    Used by API and admin views
    """

    def __init__(self, request):
        self.request = request
        self.page = None

    def collection_list(self):
        request = self.request
        self.page = safe_integer(request.GET.get('page', 1))
        filter_params = UserSearchSchema().load(request.GET.mixed()).data
        user_paginator = UserService.get_paginator(
            page=self.page,
            items_per_page=USERS_PER_PAGE,
            # url_maker gets passed to SqlalchemyOrmPage
            url_maker=lambda p: request.current_route_url(_query={"page": p}),
            filter_params=filter_params,
            db_session=request.dbsession
        )
        return user_paginator

    def user_get(self, user_id):
        request = self.request
        user = UserService.by_id(safe_integer(user_id),
                                 db_session=request.dbsession)
        if not user:
            raise pyramid.httpexceptions.HTTPNotFound()

        return user

    def populate_instance(self, instance, data):
        # this is safe and doesn't overwrite user_password with cleartext
        instance.populate_obj(data)
        log.info('user_populate_instance',
                 extra={'action': 'updated',
                        'x': datetime.now(),
                        'y': datetime.utcnow().date()})
        if data.get('password'):
            # set hashed password
            instance.set_password(data['password'])
            log.info('user_GET_PATCH', extra={'action': 'password_updated'})

    def delete(self, instance):
        log.info('user_delete', extra={'user_id': instance.id,
                                       'user_name': instance.user_name})
        instance.delete(self.request.dbsession)
        self.request.session.flash({'msg': 'User removed.',
                                    'level': 'success'})


@view_defaults(route_name='api_object', renderer='json',
               permission='admin_users',
               match_param=('object=users',))
class UserAPIView(object):
    def __init__(self, request):
        self.request = request
        self.base_view = UsersViewBase(request)

    @view_config(route_name='api_objects', request_method='GET')
    def collection_list(self):
        schema = UserCreateSchema(context={'request': self.request})
        user_paginator = self.base_view.collection_list()
        return schema.dump(user_paginator.items, many=True).data

    @view_config(route_name='api_objects', request_method='POST')
    def post(self):
        schema = UserCreateSchema(context={'request': self.request})
        data = schema.load(self.request.unsafe_json_body).data
        user = User()
        self.base_view.populate_instance(user, data)
        user.persist(flush=True, db_session=self.request.dbsession)
        return schema.dump(user).data

    @view_config(request_method='GET')
    def get(self):
        schema = UserCreateSchema(context={'request': self.request})
        user = self.base_view.user_get(self.request.matchdict['object_id'])
        return schema.dump(user).data

    @view_config(request_method="PATCH")
    def patch(self):
        user = self.base_view.user_get(self.request.matchdict['object_id'])
        schema = UserEditSchema(context={'request': self.request,
                                         'modified_obj': user})
        data = schema.load(self.request.unsafe_json_body, partial=True).data
        self.base_view.populate_instance(user, data)
        return schema.dump(user).data

    @view_config(request_method="DELETE")
    def delete(self):
        user = self.base_view.user_get(self.request.matchdict['object_id'])
        self.base_view.delete(user)
        return True
