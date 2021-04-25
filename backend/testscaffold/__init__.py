import datetime
import logging
import warnings

from datadog import statsd, initialize
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator, PHASE3_CONFIG
from pyramid.renderers import JSON
import sentry_sdk
from sentry_sdk.integrations.pyramid import PyramidIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

import testscaffold.util.cache_regions as cache_regions
import testscaffold.util.encryption as encryption
from testscaffold.celery import configure_celery
from testscaffold.security import (
    groupfinder,
    AuthTokenAuthenticationPolicy,
    PyramidSelectorPolicy,
)

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    settings.setdefault("jinja2.i18n.domain", "testscaffold")

    auth_tkt = AuthTktAuthenticationPolicy(settings["auth_tkt.seed"], callback=groupfinder)
    auth_token_policy = AuthTokenAuthenticationPolicy(callback=groupfinder)

    authorization_policy = ACLAuthorizationPolicy()

    def policy_selector(request):
        # default policy
        policy = "auth_tkt"
        # return API token policy if header is present
        if request.headers.get("x-testscaffold-auth-token"):
            policy = "auth_token_policy"
        log.info("Policy used: {}".format(policy))
        return policy

    auth_policy = PyramidSelectorPolicy(
        policy_selector=policy_selector, policies={"auth_tkt": auth_tkt, "auth_token_policy": auth_token_policy},
    )

    settings["jinja2.undefined"] = "strict"

    try:
        logging_integration = LoggingIntegration(event_level=None,)  # Do NOT send errors as events
        sentry_sdk.init(
            dsn=settings.get("sentry.dsn"),
            integrations=[
                logging_integration,
                PyramidIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
        )
    except sentry_sdk.utils.BadDsn as exc:
        log.error(f"Sentry Error {exc}")

    with Configurator(
        settings=settings,
        authentication_policy=auth_policy,
        authorization_policy=authorization_policy,
        root_factory="testscaffold.security.RootFactory",
    ) as config:

        config.include("pyramid_apispec.views")
        config.pyramid_apispec_add_explorer(spec_route_name="openapi_spec")
        config.add_translation_dirs("testscaffold:locale/", "wtforms:locale/")

        # modify json renderer
        json_renderer = JSON(indent=4)

        def datetime_adapter(obj, request):
            return obj.isoformat()

        json_renderer.add_adapter(datetime.datetime, datetime_adapter)
        json_renderer.add_adapter(datetime.date, datetime_adapter)
        config.add_renderer("json", json_renderer)

        # set crypto key used to store sensitive data like auth tokens
        encryption.ENCRYPTION_SECRET = settings["encryption_secret"]
        # CSRF is enabled by defualt
        # use X-XSRF-TOKEN for angular
        # config.set_default_csrf_options(require_csrf=True, header='X-XSRF-TOKEN')
        config.add_view_deriver("testscaffold.predicates.auth_token_aware_csrf_view", name="csrf_view")

        config.include("pyramid_mailer")
        config.include("pyramid_jinja2")
        config.include("pyramid_beaker")
        config.include("ziggurat_foundations.ext.pyramid.sign_in")

        # make request.user available
        config.add_request_method("testscaffold.util.request:get_user", "user", reify=True)
        config.add_request_method("testscaffold.util.request:safe_json_body", "safe_json_body", reify=True)
        config.add_request_method("testscaffold.util.request:unsafe_json_body", "unsafe_json_body", reify=True)
        config.add_request_method("testscaffold.util.request:get_authomatic", "authomatic", reify=True)

        config.add_view_predicate("context_type_class", "testscaffold.predicates.ContextTypeClass")

        config.scan("testscaffold.events")
        config.scan("testscaffold.subscribers")
        config.include("testscaffold.models")
        config.include("testscaffold.routes")
        config.include("testscaffold.views")

        # configure celery in later phase
        def wrap_config_celery():
            configure_celery(config.registry.settings)

        config.action(None, wrap_config_celery, order=PHASE3_CONFIG + 999)

        # setup dogpile cache
        cache_regions.regions = cache_regions.CacheRegions(settings)
        config.registry.cache_regions = cache_regions.regions

        # setup statsd
        statsd_url = settings.get("monitoring.statsd", "127.0.0.1:8125")
        statsd_host, statsd_port = statsd_url.split(":")
        options = {"statsd_host": statsd_host, "statsd_port": int(statsd_port)}
        initialize(**options)
        statsd.namespace = "testscaffold"
        statsd.use_ms = True
        # statsd.constant_tags = [f"branch:{settings['branch']}"]
        config.registry.statsd_client = statsd

        if not config.registry.settings.get("testscaffold.ignore_warnings", True):
            warnings.filterwarnings("default")

    return config.make_wsgi_app()
