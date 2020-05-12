# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import traceback
import sys
from datetime import timedelta

from celery import Celery
from celery.bin import Option
from celery.exceptions import WorkerTerminate
from celery.signals import task_prerun, task_retry, task_failure, task_success
from celery.signals import task_revoked, user_preload_options
from kombu.serialization import register
from pyramid.paster import bootstrap
from pyramid.request import Request
from pyramid.scripting import prepare
from pyramid.settings import asbool
from pyramid.threadlocal import get_current_request

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
    "worker_max_tasks_per_child": 1000,
    "task_ignore_result": True,
    "accept_content": ("date_json",),
    "task_serializer": "date_json",
    "result_serializer": "date_json",
    "broker_url": None,
    "worker_concurrency": None,
    "timezone": None,
    "beat_schedule": {"name": {"task": "task", "schedule": timedelta(seconds=5)}},
}

celery = Celery()
celery.config_from_object(CELERY_CONFIG)

celery.user_options["preload"].add(
    Option(
        "--ini",
        dest="ini",
        default=None,
        help="Specifies pyramid configuration file location.",
    )
)


def on_preload_parsed(options, app, **kwargs):
    """
    This actually configures celery from pyramid config file
    """
    celery.conf["INI_PYRAMID"] = options["ini"][0]
    ini_location = options["ini"][0]
    if not ini_location:
        raise Exception(
            "You need to pass pyramid ini location using "
            "--ini=filename.ini argument to the worker"
        )
    env = bootstrap(ini_location)
    # register error handling here
    celery.pyramid = env


@user_preload_options.connect
def on_preload_parsed_wrapper(options, app, **kwargs):
    """
    Ugly hack for celery swallowing exceptions here
    """
    try:
        on_preload_parsed(options, app, **kwargs)
    except Exception as exc:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        raise WorkerTerminate("Terminating worker!")


def configure_celery(pyramid_registry):
    settings = pyramid_registry.settings
    CELERY_CONFIG["broker_url"] = settings["celery.broker_url"]
    CELERY_CONFIG["worker_concurrency"] = settings["celery.concurrency"]
    CELERY_CONFIG["timezone"] = settings["celery.timezone"]
    if asbool(settings.get("celery.always_eager")):
        CELERY_CONFIG["task_always_eager"] = True
        CELERY_CONFIG["task_eager_propagates"] = True

    celery.config_from_object(CELERY_CONFIG)


@task_prerun.connect
def task_prerun_signal(task_id, task, args, kwargs, **kwaargs):
    if hasattr(celery, "pyramid"):
        env = celery.pyramid
        env = prepare(registry=env["request"].registry)
        proper_base_url = env["request"].registry.settings["base_url"]
        tmp_request = Request.blank("/", base_url=proper_base_url)
        # ensure tasks generate url for right domain from config
        env["request"].environ["HTTP_HOST"] = tmp_request.environ["HTTP_HOST"]
        env["request"].environ["SERVER_PORT"] = tmp_request.environ["SERVER_PORT"]
        env["request"].environ["SERVER_NAME"] = tmp_request.environ["SERVER_NAME"]
        env["request"].environ["wsgi.url_scheme"] = tmp_request.environ[
            "wsgi.url_scheme"
        ]
    get_current_request().tm.begin()


@task_success.connect
def task_success_signal(result, **kwargs):
    get_current_request().tm.commit()
    if hasattr(celery, "pyramid"):
        celery.pyramid["closer"]()


@task_retry.connect
def task_retry_signal(request, reason, einfo, **kwargs):
    get_current_request().tm.abort()
    if hasattr(celery, "pyramid"):
        celery.pyramid["closer"]()


@task_failure.connect
def task_failure_signal(task_id, exception, args, kwargs, traceback, einfo, **kwaargs):
    get_current_request().tm.abort()
    if hasattr(celery, "pyramid"):
        celery.pyramid["closer"]()


@task_revoked.connect
def task_revoked_signal(request, terminated, signum, expired, **kwaargs):
    get_current_request().tm.abort()
    if hasattr(celery, "pyramid"):
        celery.pyramid["closer"]()
