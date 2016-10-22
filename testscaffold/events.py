# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class EmailEvent(object):
    """ When emitted the application will send email to recipients that is
    generated from specified template
    """

    def __init__(self, request, recipients, tmpl_vars, tmpl_loc,
                 send_immediately=False, fail_silently=False):
        self.request = request
        self.recipients = recipients
        self.tmpl_vars = tmpl_vars
        self.tmpl_loc = tmpl_loc
        self.send_immediately = send_immediately
        self.fail_silently = fail_silently


class SocialAuthEvent(object):
    """ When emitted the application will add or update the tokens for
    specified user and provider
    """

    def __init__(self, request, user, social_data):
        self.request = request
        self.user = user
        self.social_data = social_data
