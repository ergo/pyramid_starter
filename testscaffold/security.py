# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import structlog

from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from pyramid.authentication import CallbackAuthenticationPolicy
from ziggurat_foundations.permissions import permission_to_pyramid_acls

from testscaffold.services.auth_token import AuthTokenService
from testscaffold.services.user import UserService


log = structlog.getLogger(__name__)


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
                    found=True,
                    owner=auth_token.owner_id)
                return auth_token.owner_id
            log.info('AuthTokenAuthenticationPolicy.unauthenticated_userid',
                        found=False, owner=None)

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


class RootFactory(object):
    """
    General factory for non-resource specific pages, returns an empty
    context object that will list permissions ONLY for the user specific
    to this request from ziggurat
    """

    def __init__(self, request):
        self.__acl__ = []
        # general page factory - append custom non resource permissions
        if hasattr(request, 'user') and request.user:
            permissions = UserService.permissions(request.user,
                                                  db_session=request.dbsession)
            for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                    permissions):
                self.__acl__.append(
                    rewrite_root_perm(outcome, perm_user, perm_name))
