# -*- coding: utf-8 -*-
import logging


from celery import Celery, signals
from click import Option
from kombu.serialization import register
from pyramid.paster import bootstrap
from pyramid.scripting import prepare
from pyramid.settings import asbool
from pyramid.threadlocal import get_current_request, get_current_registry

from testscaffold.celery.encoders import json_dumps, json_loads

log = logging.getLogger(__name__)

register(
    "date_json",
    json_dumps,
    json_loads,
    content_type="application/x-date_json",
    content_encoding="utf-8",
)

CELERY_CONFIG = {
    "imports": ("testscaffold.celery.tasks",),
    "task_time_limit": 300,
    "worker_max_tasks_per_child": 10000,
    "accept_content": ("date_json",),
    "task_serializer": "date_json",
    "result_serializer": "date_json",
    "broker_url": None,
    # broker should timeout
    "broker_transport_options": {
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    "worker_concurrency": None,
    "timezone": "UTC",
    "beat_schedule": {
        "heartbeat-celery-30-seconds": {
            "task": "testscaffold.celery.tasks.celery_beat_heartbeat",
            "schedule": 30.0,
        },
    },
}

celery_app = Celery()
celery_app.user_options["preload"].add(
    Option(
        ("--ini",),
        default=None,
        help="Specifies pyramid configuration file location.",
    )
)
celery_app.config_from_object(CELERY_CONFIG)


@signals.user_preload_options.connect
def on_preload_parsed(options, app, **kwargs):
    """
    This actually configures celery from pyramid config file
    """
    celery_app.conf["INI_PYRAMID"] = options["ini"]
    ini_location = options["ini"]
    if not ini_location:
        raise Exception(
            "You need to pass pyramid ini location using "
            "--ini=filename.ini argument to the worker"
        )
    env = bootstrap(ini_location)
    # register error handling here
    celery_app.pyramid = env


def configure_celery(settings):
    settings = settings
    CELERY_CONFIG["broker_url"] = settings["celery.broker_url"]

    if settings.get("celery.cache_backend"):
        CELERY_CONFIG["cache_backend"] = settings["celery.cache_backend"]
    elif settings.get("celery.result_backend"):
        CELERY_CONFIG["result_backend"] = settings["celery.result_backend"]

    if settings.get("celery.concurrency"):
        CELERY_CONFIG["worker_concurrency"] = int(settings["celery.concurrency"])
    if settings.get("celery.timezone"):
        CELERY_CONFIG["timezone"] = settings["celery.timezone"]

    if asbool(settings.get("celery.always_eager")):
        # WARNING: NEVER ENABLE IN PRODUCTION: enable to disable async task execution locally for celery
        CELERY_CONFIG["task_always_eager"] = True
        CELERY_CONFIG["task_eager_propagates"] = True
    log.info("Configuring celery from ini file")
    celery_app.config_from_object(CELERY_CONFIG)


@signals.after_task_publish.connect
def task_after_task_publish(signal, sender, *args, **kwargs):
    registry = get_current_registry()
    registry.statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:after_task_publish"]
    )


@signals.task_prerun.connect
def task_prerun(signal, sender, *args, **kwargs):
    log.debug("task prerun %s" % sender.name)
    env = celery_app.pyramid
    env = prepare(registry=env["request"].registry)
    env["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:prerun"]
    )


@signals.task_retry.connect
def task_retry_signal(request, reason, einfo, **kwargs):
    log.debug("task retry")
    request = get_current_request()
    abort_transaction(request)
    celery_app.pyramid["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:retry"]
    )
    celery_app.pyramid["closer"]()


@signals.task_revoked.connect
def task_revoked_signal(request, terminated, signum, expired, **kwaargs):
    log.debug("task revoked")
    request = get_current_request()
    abort_transaction(request)
    celery_app.pyramid["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:revoked"]
    )
    celery_app.pyramid["closer"]()


@signals.task_success.connect
def task_ok(signal, sender, **result):
    log.debug("task %s finished" % sender.name)
    request = get_current_request()
    abort_transaction(request)
    celery_app.pyramid["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:success"]
    )
    celery_app.pyramid["closer"]()


@signals.task_postrun.connect
def task_postrun_log(signal, sender, task_id, task, args, kwargs, retval, state, **kw):
    log.debug("task %s postrun %s" % (sender.name, state))
    celery_app.pyramid["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:postrun"]
    )
    celery_app.pyramid["closer"]()


@signals.task_failure.connect
def task_failed(
    signal, sender, task_id, exception, args, kwargs, traceback, einfo, **kw
):
    log.info("task %s FAILED" % sender.name)
    request = get_current_request()
    abort_transaction(request)
    celery_app.pyramid["registry"].statsd_client.increment(
        "queue_tasks_count", 1, tags=["signal:failed"]
    )
    celery_app.pyramid["closer"]()


def abort_transaction(request):
    try:
        request.tm.abort()
    except NoTransaction:
        pass
