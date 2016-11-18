# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from datetime import datetime, timedelta

from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config, view_defaults
from testscaffold.celery.tasks import test_task
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


@view_defaults(route_name='admin_objects', permission='admin_celery')
class CeleryAdminView(BaseView):

    @view_config(renderer='testscaffold:templates/admin/celery.jinja2',
                 match_param=('object=celery', 'verb=GET'))
    def index(self):
        return {}

    @view_config(renderer='testscaffold:templates/admin/celery.jinja2',
                 match_param=('object=celery', 'verb=POST'))
    def task_send(self):
        request = self.request
        log.info('send_task', extra={'action': 'task_sent'})
        d = datetime.utcnow()
        td = timedelta(days=7, seconds=6, microseconds=5,
                       milliseconds=4, minutes=3, hours=2, weeks=1)
        test_task.delay('python', d, d.date(), td)
        request.session.flash(
            {'msg': self.translate(_('Task sent')), 'level': 'success'})
        return {}
