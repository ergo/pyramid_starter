# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from pyramid.threadlocal import get_current_request
from wtforms.ext.csrf.form import SecureForm

from pyramid.exceptions import BadCSRFToken


class ZigguratForm(SecureForm):
    schema_instance = None

    def __init__(self, formdata=None, obj=None, prefix='', context=None,
                 **kwargs):
        """
        :param formdata:
        :param obj:
        :param prefix:
        :param csrf_context: Optional extra data which is passed
        transparently to your CSRF implementation.
        :param context: Optional extra data which may be handy later in
        validation and processing
        :param kwargs:
        :return:
        """
        super(SecureForm, self).__init__(formdata, obj, prefix, **kwargs)
        self.context = context
        self.csrf_token.current_token = self.generate_csrf_token(
            self.context.get('request'))
        self.obj = obj

    def generate_csrf_token(self, csrf_context):
        if not csrf_context:
            csrf_context = get_current_request()
        return csrf_context.session.get_csrf_token()

    def validate_csrf_token(self, field):
        if field.data != field.current_token:
            raise BadCSRFToken()
