# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from pyramid.exceptions import HTTPNotFound
from pyramid.authentication import CallbackAuthenticationPolicy
from ziggurat_foundations.models.services.resource import ResourceService
from ziggurat_foundations.permissions import permission_to_pyramid_acls

from testscaffold.util import safe_integer
from testscaffold.services.auth_token import AuthTokenService
from testscaffold.services.user import UserService

log = logging.getLogger(__name__)


def groupfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        groups = ['group:%s' % g.id for g in request.user.groups]
        return groups
    return []


class AuthTokenAuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback=None):
        self.callback = callback

    def remember(self, request, principal, **kw):
        return []

    def forget(self, request):
        return []

    def unauthenticated_userid(self, request):
        token = u'{}'.format(
            request.headers.get('x-testscaffold-auth-token', '')
        )
        if token:
            auth_token = AuthTokenService.by_token(
                token, db_session=request.dbsession)
            if auth_token:
                log.info(
                    'AuthTokenAuthenticationPolicy.unauthenticated_userid',
                    extra={'found': True, 'owner': auth_token.owner_id})
                return auth_token.owner_id
            log.info('AuthTokenAuthenticationPolicy.unauthenticated_userid',
                     extra={'found': False, 'owner': None})

    def authenticated_userid(self, request):
        return self.unauthenticated_userid(request)


def rewrite_root_perm(outcome, perm_user, perm_name):
    """
    Translates root_administration into ALL_PERMISSIONS object
    """
    if perm_name == 'root_administration':
        return outcome, perm_user, ALL_PERMISSIONS
    else:
        return outcome, perm_user, perm_name


def allow_root_access(request, context):
    """
    Adds ALL_PERMISSIONS to every resource if user has 'root_permission'
    """
    if getattr(request, 'user'):
        for perm in permission_to_pyramid_acls(request.user.permissions):
            if perm[2] == 'root_administration':
                context.__acl__.append(
                    (perm[0], perm[1], ALL_PERMISSIONS))


def object_security_factory(request):
    object_type = request.matchdict['object']
    # fetch deta
    if object_type in ['resources', 'entries']:
        return DefaultResourceFactory(request)

    return RootFactory(request)


def filter_admin_panel_perms(item):
    if str(item[2]).startswith('admin_'):
        return False
    return True


class RootFactory(object):
    """
    General factory for non-resource specific pages, returns an empty
    context object that will list permissions ONLY for the user specific
    to this request from ziggurat
    """

    def __init__(self, request):
        self.__acl__ = []
        # general page factory - append custom non resource permissions
        if getattr(request, 'user'):
            permissions = UserService.permissions(request.user,
                                                  db_session=request.dbsession)
            has_admin_panel_access = False
            panel_perms = ['admin_panel', ALL_PERMISSIONS]
            for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                    permissions):
                perm_tuple = rewrite_root_perm(outcome, perm_user, perm_name)
                if perm_tuple[0] is Allow and perm_tuple[2] in panel_perms:
                    has_admin_panel_access = True
                self.__acl__.append(perm_tuple)

            # users have special permission called `admin_panel`
            # it should be prerequisite for other `admin*` permissions
            # if it is not present let's deny other admin permissions
            if not has_admin_panel_access:
                self.__acl__ = list(filter(
                    filter_admin_panel_perms, self.__acl__
                ))


class DefaultResourceFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        resource_id = safe_integer(request.matchdict.get("object_id"))
        self.resource = ResourceService.by_resource_id(
            resource_id, db_session=request.dbsession)
        if not self.resource:
            raise HTTPNotFound()

        if self.resource:
            self.__acl__ = self.resource.__acl__

        if self.resource and request.user:
            # add perms that this user has for this resource
            # this is a big performance optimization - we fetch only data
            # needed to check one specific user
            permissions = ResourceService.perms_for_user(
                self.resource, request.user)
            for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                    permissions):
                self.__acl__.append(
                    rewrite_root_perm(outcome, perm_user, perm_name))

        allow_root_access(request, context=self)
