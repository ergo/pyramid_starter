# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import warnings

from pyramid_authstack import AuthenticationStackPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator, PHASE3_CONFIG
from pyramid.renderers import JSON

import testscaffold.util.cache_regions as cache_regions
import testscaffold.util.encryption as encryption
from testscaffold.celery import configure_celery
from testscaffold.security import groupfinder, AuthTokenAuthenticationPolicy


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    stacked_policy = AuthenticationStackPolicy()
    auth_tkt = AuthTktAuthenticationPolicy(settings['auth_tkt.seed'],
                                           callback=groupfinder)
    auth_token_policy = AuthTokenAuthenticationPolicy(callback=groupfinder)

    stacked_policy.add_policy('auth_tkt', auth_tkt)
    stacked_policy.add_policy('auth_token', auth_token_policy)
    authorization_policy = ACLAuthorizationPolicy()

    settings['jinja2.undefined'] = 'strict'
    config = Configurator(settings=settings,
                          authentication_policy=stacked_policy,
                          authorization_policy=authorization_policy,
                          root_factory='testscaffold.security.RootFactory')
    # modify json renderer
    json_renderer = JSON(indent=4)

    def datetime_adapter(obj, request):
        return obj.isoformat()

    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(datetime.date, datetime_adapter)
    config.add_renderer('json', json_renderer)

    # set crypto key used to store sensitive data like auth tokens
    encryption.ENCRYPTION_SECRET = settings['encryption_secret']
    # CSRF is enabled by defualt
    # use X-XSRF-TOKEN for angular
    config.set_default_csrf_options(require_csrf=True, header='X-XSRF-TOKEN')
    config.add_view_deriver(
        'testscaffold.predicates.auth_token_aware_csrf_view',
        name='csrf_view')

    config.include('pyramid_mailer')
    config.include('pyramid_jinja2')
    config.include('pyramid_redis_sessions')
    config.include('ziggurat_foundations.ext.pyramid.sign_in')

    # make request.user available
    config.add_request_method(
        'testscaffold.util.request:get_user', 'user', reify=True)
    config.add_request_method(
        'testscaffold.util.request:safe_json_body', 'safe_json_body',
        reify=True)
    config.add_request_method(
        'testscaffold.util.request:unsafe_json_body', 'unsafe_json_body',
        reify=True)
    config.add_request_method(
        'testscaffold.util.request:get_authomatic', 'authomatic',
        reify=True)

    config.add_view_predicate('context_type_class',
                              'testscaffold.predicates.contextTypeClass')

    config.include('testscaffold.models')
    config.include('testscaffold.routes')
    config.scan(ignore=['testscaffold.migrations', 'testscaffold.tests',
                        'testscaffold.scripts'])

    # configure celery in later phase
    def wrap_config_celery():
        configure_celery(config.registry)

    config.action(None, wrap_config_celery, order=PHASE3_CONFIG + 999)

    # setup dogpile cache
    cache_regions.regions = cache_regions.CacheRegions(settings)
    config.registry.cache_regions = cache_regions.regions

    if not config.registry.settings.get('testscaffold.ignore_warnings', True):
        warnings.filterwarnings('default')

    return config.make_wsgi_app()
