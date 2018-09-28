# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from pyramid.exceptions import BadCSRFToken
from pyramid.i18n import TranslationStringFactory
from pyramid.threadlocal import get_current_request
from wtforms import Form
from wtforms.csrf.core import CSRF

_ = TranslationStringFactory("wtforms")


class PyramidCSRF(CSRF):
    """
    Reuse tokens from pyramid session
    """

    def setup_form(self, form):
        request = form.context.get("request")
        if request:
            self.csrf_context = request
        else:
            self.csrf_context = get_current_request()
        return super(PyramidCSRF, self).setup_form(form)

    def generate_csrf_token(self, csrf_token):
        return self.csrf_context.session.get_csrf_token()

    def validate_csrf_token(self, form, field):
        if field.data != field.current_token:
            raise BadCSRFToken("Invalid CSRF token")


class PyramidTranslator(object):
    """
    Uses pyramid translation machinery for wtforms INTERNAL translation strings
    """

    def __init__(self, request, domain=None):
        self.translate = request.localizer.translate
        self.pluralize = request.localizer.pluralize
        self.domain = domain

    def gettext(self, string):
        return self.translate(_(string))

    def ngettext(self, singular, plural, n):
        return self.pluralize(singular, plural, n)


class ZigguratForm(Form):
    class Meta:
        csrf = True
        csrf_class = PyramidCSRF

        def get_translations(self, form):
            """
            This will translate internal wtform validators for us
            """
            request = form.context.get("request") or get_current_request()
            return PyramidTranslator(request)

    def __init__(self, formdata=None, obj=None, prefix="", context=None, **kwargs):
        """
        :param formdata:
        :param obj:
        :param prefix:
        :param context: Optional extra data which may be handy later in
        validation and processing
        :param kwargs:
        :return:
        """
        self.context = context
        self.obj = obj
        super(ZigguratForm, self).__init__(formdata, obj, prefix, **kwargs)

    def form_translator(self, string):
        """
        Used to translate our in-app form messages and field names
        It is required because for example marshmallow validator messages will
        lose metadata (is there any easy fix for that?)
        :param string:
        :return:
        """
        request = self.context.get("request") or get_current_request()
        return request.localizer.translate(_(string), domain="testscaffold")
