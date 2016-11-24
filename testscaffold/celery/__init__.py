# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
from datetime import timedelta

from celery import Celery
from celery.bin import Option
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

register('date_json', json_dumps, json_loads,
         content_type='application/x-date_json',
         content_encoding='utf-8')

CELERY_CONFIG = {
    'CELERY_IMPORTS': ("testscaffold.celery.tasks",),
    'CELERYD_TASK_TIME_LIMIT': 300,
    'CELERYD_MAX_TASKS_PER_CHILD': 1000,
    'CELERY_IGNORE_RESULT': True,
    'CELERY_ACCEPT_CONTENT': ('date_json',),
    'CELERY_TASK_SERIALIZER': 'date_json',
    'CELERY_RESULT_SERIALIZER': 'date_json',
    'BROKER_URL': None,
    'CELERYD_CONCURRENCY': None,
    'CELERY_TIMEZONE': None,
    'CELERYBEAT_SCHEDULE': {
        'name': {
            'task': 'task',
            'schedule': timedelta(seconds=5)
        }
    }
}

celery = Celery()
celery.config_from_object(CELERY_CONFIG)

celery.user_options['preload'].add(
    Option('--ini', dest='ini', default=None,
           help='Specifies pyramid configuration file location.')
)


@user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    """
    This actually configures celery from pyramid config file
    """
    celery.conf['INI_PYRAMID'] = options['ini']
    ini_location = options['ini']
    if not ini_location:
        raise Exception('You need to pass pyramid ini location using '
                        '--ini=filename.ini argument to the worker')
    env = bootstrap(ini_location)
    try:
        import appenlight_client.client as appenlight_client
        from appenlight_client.ext.celery import register_signals
        api_key = env['request'].registry.settings['appenlight.api_key']
        tr_config = env['request'].registry.settings.get(
            'appenlight.transport_config')
        config = appenlight_client.get_config({'appenlight.api_key': api_key})
        if tr_config:
            config['appenlight.transport_config'] = tr_config
        appenlight_client = appenlight_client.Client(config)
        register_signals(appenlight_client)
    except ImportError:
        pass

    celery.pyramid = env


def configure_celery(pyramid_registry):
    settings = pyramid_registry.settings
    CELERY_CONFIG['BROKER_URL'] = settings['celery.broker_url']
    CELERY_CONFIG['CELERYD_CONCURRENCY'] = settings['celery.concurrency']
    CELERY_CONFIG['CELERY_TIMEZONE'] = settings['celery.timezone']
    if asbool(settings.get('celery.always_eager')):
        CELERY_CONFIG['CELERY_ALWAYS_EAGER'] = True
        CELERY_CONFIG['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = True

    celery.config_from_object(CELERY_CONFIG)


@task_prerun.connect
def task_prerun_signal(task_id, task, args, kwargs, **kwaargs):
    if hasattr(celery, 'pyramid'):
        env = celery.pyramid
        env = prepare(registry=env['request'].registry)
        proper_base_url = env['request'].registry.settings['base_url']
        tmp_request = Request.blank('/', base_url=proper_base_url)
        # ensure tasks generate url for right domain from config
        env['request'].environ['HTTP_HOST'] = tmp_request.environ['HTTP_HOST']
        env['request'].environ['SERVER_PORT'] = tmp_request.environ[
            'SERVER_PORT']
        env['request'].environ['SERVER_NAME'] = tmp_request.environ[
            'SERVER_NAME']
        env['request'].environ['wsgi.url_scheme'] = tmp_request.environ[
            'wsgi.url_scheme']
    get_current_request().tm.begin()


@task_success.connect
def task_success_signal(result, **kwargs):
    get_current_request().tm.commit()
    if hasattr(celery, 'pyramid'):
        celery.pyramid["closer"]()


@task_retry.connect
def task_retry_signal(request, reason, einfo, **kwargs):
    get_current_request().tm.abort()
    if hasattr(celery, 'pyramid'):
        celery.pyramid["closer"]()


@task_failure.connect
def task_failure_signal(task_id, exception, args, kwargs, traceback, einfo,
                        **kwaargs):
    get_current_request().tm.abort()
    if hasattr(celery, 'pyramid'):
        celery.pyramid["closer"]()


@task_revoked.connect
def task_revoked_signal(request, terminated, signum, expired, **kwaargs):
    get_current_request().tm.abort()
    if hasattr(celery, 'pyramid'):
        celery.pyramid["closer"]()
