# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

from pyramid.interfaces import IDefaultCSRFOptions
from pyramid.session import (
    check_csrf_origin,
    check_csrf_token,
)

log = logging.getLogger(__name__)


# taken directly from pyramid 1.7
# pyramid/viewderivers.py
# the difference is this deriver will ignore csrf_check when auth token
# policy is in effect

def auth_token_aware_csrf_view(view, info):
    explicit_val = info.options.get('require_csrf')
    defaults = info.registry.queryUtility(IDefaultCSRFOptions)
    if defaults is None:
        default_val = False
        token = 'csrf_token'
        header = 'X-CSRF-Token'
        safe_methods = frozenset(["GET", "HEAD", "OPTIONS", "TRACE"])
    else:
        default_val = defaults.require_csrf
        token = defaults.token
        header = defaults.header
        safe_methods = defaults.safe_methods
    enabled = (
        explicit_val is True or
        (explicit_val is not False and default_val)
    )
    # disable if both header and token are disabled
    enabled = enabled and (token or header)
    wrapped_view = view
    if enabled:
        def csrf_view(context, request):
            is_from_auth_token = 'auth:auth_token' in \
                                 request.effective_principals
            if is_from_auth_token:
                log.debug('ignoring CSRF check, auth token used')
            elif (request.method not in safe_methods and (
                            getattr(request, 'exception', None) is None
                    or explicit_val is not None)):
                check_csrf_origin(request, raises=True)
                check_csrf_token(request, token, header, raises=True)
            return view(context, request)

        wrapped_view = csrf_view
    return wrapped_view


auth_token_aware_csrf_view.options = ('require_csrf',)


class ContextTypeClass(object):
    """
    Passes only if context objects are of types specified in context properties
    """

    def __init__(self, context_properties, config):
        self.context_properties = context_properties

    def text(self):
        return u'context_type_class = %s' % self.context_properties

    phash = text

    def __call__(self, context, request):
        for key_name, cls in self.context_properties.values():
            to_check = getattr(context, key_name, None)
            if not isinstance(to_check, cls):
                return False
        return True
