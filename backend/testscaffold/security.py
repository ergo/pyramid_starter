import logging

from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.exceptions import HTTPNotFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Allow, ALL_PERMISSIONS
from ziggurat_foundations.permissions import permission_to_pyramid_acls
from zope.interface import implementer

from testscaffold.services.resource import ResourceService
from testscaffold.services.auth_token import AuthTokenService
from testscaffold.services.user import UserService
from testscaffold.util import safe_integer

log = logging.getLogger(__name__)


def groupfinder(userid, request):
    # registers _reified_user_obj that will be grabbed later by request.user property
    # we cache it so we don't have to query the db more than once
    if not getattr(request, "_reified_user_obj", None) and userid:
        user = UserService.get(userid, db_session=request.dbsession)
        request._reified_user_obj = user
    elif userid:
        user = request._reified_user_obj
    if user:
        groups = ["group:%s" % g.id for g in user.groups]
        return groups


@implementer(IAuthenticationPolicy)
class PyramidSelectorPolicy:
    def __init__(self, policy_selector=None, policies=None):
        """
        Policy factory - a callable that accepts argument ``request`` and
        decides which policy instance should be returned based on that.
        That name will be added to request object as an attribute ``matched_auth_policy``.
        The factory should always return a policy.

        Example usage::

            auth_tkt = AuthTktAuthenticationPolicy(...)
            auth_token_policy = AuthTokenAuthenticationPolicy(...)

            def policy_selector(request):
                # default policy
                policy = "auth_tkt"
                # return API token policy if header is present
                if request.headers.get("x-testscaffold-auth-token"):
                    policy = "auth_token_policy"
                log.info("Policy used: {}".format(policy))
                return policy

            auth_policy = PyramidSelectorPolicy(
                policy_selector=policy_selector,
                policies={
                    "auth_tkt": auth_tkt,
                    "auth_token_policy": auth_token_policy
                }
            )
            Configurator(settings=settings, authentication_policy=auth_policy,...)

        :param policy_factory:
        """
        self.policy_selector = policy_selector
        self.policies = policies

    def _get_policy(self, request, policy_key):
        if policy_key not in self.policies:
            raise ValueError(
                "Policy {} is not found in PyramidSelectorPolicy".format(policy_key)
            )
        request.matched_auth_policy = policy_key
        return self.policies[policy_key]

    def authenticated_userid(self, request):
        """ Return the authenticated :term:`userid` or ``None`` if
        no authenticated userid can be found. This method of the
        policy should ensure that a record exists in whatever
        persistent store is used related to the user (the user
        should not have been deleted); if a record associated with
        the current id does not exist in a persistent store, it
        should return ``None``.
        """
        policy = self._get_policy(request, self.policy_selector(request))
        return policy.authenticated_userid(request)

    def unauthenticated_userid(self, request):
        """ Return the *unauthenticated* userid.  This method
        performs the same duty as ``authenticated_userid`` but is
        permitted to return the userid based only on data present
        in the request; it needn't (and shouldn't) check any
        persistent store to ensure that the user record related to
        the request userid exists.

        This method is intended primarily a helper to assist the
        ``authenticated_userid`` method in pulling credentials out
        of the request data, abstracting away the specific headers,
        query strings, etc that are used to authenticate the request.
        """
        policy = self._get_policy(request, self.policy_selector(request))
        return policy.unauthenticated_userid(request)

    def effective_principals(self, request):
        """ Return a sequence representing the effective principals
        typically including the :term:`userid` and any groups belonged
        to by the current user, always including 'system' groups such
        as ``pyramid.security.Everyone`` and
        ``pyramid.security.Authenticated``.
        """
        policy = self._get_policy(request, self.policy_selector(request))
        return policy.effective_principals(request)

    def remember(self, request, userid, **kw):
        """ Return a set of headers suitable for 'remembering' the
        :term:`userid` named ``userid`` when set in a response.  An
        individual authentication policy and its consumers can
        decide on the composition and meaning of **kw.
        """
        policy = self._get_policy(request, self.policy_selector(request))
        return policy.remember(request, userid, **kw)

    def forget(self, request):
        """ Return a set of headers suitable for 'forgetting' the
        current user on subsequent requests.
        """
        policy = self._get_policy(request, self.policy_selector(request))
        return policy.forget(request)


class AuthTokenAuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback=None):
        self.callback = callback

    def remember(self, request, principal, **kw):
        return []

    def forget(self, request):
        return []

    def unauthenticated_userid(self, request):
        token = "{}".format(request.headers.get("x-testscaffold-auth-token", ""))
        if token:
            auth_token = AuthTokenService.by_token(token, db_session=request.dbsession)
            if auth_token:
                log.info(
                    "AuthTokenAuthenticationPolicy.unauthenticated_userid",
                    extra={"found": True, "owner": auth_token.owner_id},
                )
                return auth_token.owner_id
            log.info(
                "AuthTokenAuthenticationPolicy.unauthenticated_userid",
                extra={"found": False, "owner": None},
            )


def rewrite_root_perm(outcome, perm_user, perm_name):
    """
    Translates root_administration into ALL_PERMISSIONS object
    """
    if perm_name == "root_administration":
        return outcome, perm_user, ALL_PERMISSIONS
    else:
        return outcome, perm_user, perm_name


def allow_root_access(request, context):
    """
    Adds ALL_PERMISSIONS to every resource if user has 'root_permission'
    """
    if getattr(request, "user"):
        permissions = UserService.permissions(request.user)
        for perm in permission_to_pyramid_acls(permissions):
            if perm[2] == "root_administration":
                context.__acl__.append((perm[0], perm[1], ALL_PERMISSIONS))


def object_security_factory(request):
    object_type = request.matchdict["object"]
    # fetch deta
    if object_type in ["resources", "entries"]:
        return DefaultResourceFactory(request)

    return RootFactory(request)


def filter_admin_panel_perms(item):
    if str(item[2]).startswith("admin_"):
        return False
    return True


class RootFactory:
    """
    General factory for non-resource specific pages, returns an empty
    context object that will list permissions ONLY for the user specific
    to this request from ziggurat
    """

    def __init__(self, request):
        self.__acl__ = []
        # general page factory - append custom non resource permissions
        if getattr(request, "user"):
            permissions = UserService.permissions(
                request.user, db_session=request.dbsession
            )
            has_admin_panel_access = False
            panel_perms = ["admin_panel", ALL_PERMISSIONS]
            for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                permissions
            ):
                perm_tuple = rewrite_root_perm(outcome, perm_user, perm_name)
                if perm_tuple[0] is Allow and perm_tuple[2] in panel_perms:
                    has_admin_panel_access = True
                self.__acl__.append(perm_tuple)

            # users have special permission called `admin_panel`
            # it should be prerequisite for other `admin*` permissions
            # if it is not present let's deny other admin permissions
            if not has_admin_panel_access:
                self.__acl__ = list(filter(filter_admin_panel_perms, self.__acl__))


class DefaultResourceFactory:
    def __init__(self, request):
        self.__acl__ = []
        resource_id = safe_integer(request.matchdict.get("object_id"))
        self.resource = ResourceService.by_resource_id(
            resource_id, db_session=request.dbsession
        )
        if not self.resource:
            raise HTTPNotFound()

        if self.resource:
            self.__acl__ = self.resource.__acl__

        if self.resource and request.user:
            # add perms that this user has for this resource
            # this is a big performance optimization - we fetch only data
            # needed to check one specific user
            permissions = ResourceService.perms_for_user(self.resource, request.user)
            for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                permissions
            ):
                self.__acl__.append(rewrite_root_perm(outcome, perm_user, perm_name))

        allow_root_access(request, context=self)
