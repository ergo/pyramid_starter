# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
from pyramid.events import subscriber, BeforeRender, NewRequest
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from ziggurat_foundations.models.services.external_identity import \
    ExternalIdentityService

from testscaffold.events import EmailEvent, SocialAuthEvent
from testscaffold.models.external_identity import ExternalIdentity
from testscaffold.validation.forms import UserLoginForm


@subscriber(EmailEvent)
def email_handler(event):
    mailer = get_mailer(event.request)
    settings = event.request.registry.settings
    rendered = render(event.tmpl_loc, event.tmpl_vars,
                      request=event.request)
    message = Message(subject=event.tmpl_vars['email_title'],
                      sender=settings['mailing.from_email'],
                      recipients=event.recipients,
                      html=rendered)
    if not event.send_immediately:
        mailer.send(message)
    else:
        mailer.send_immediately(message, fail_silently=event.fail_silently)


@subscriber(SocialAuthEvent)
def handle_social_data(event):
    social_data = event.social_data
    request = event.request

    if not social_data['user']['id']:
        request.session.flash(
            'No external user id found? Perhaps permissions for '
            'authentication are set incorrectly', 'error')
        return False

    extng_id = ExternalIdentityService.by_external_id_and_provider(
        social_data['user']['id'],
        social_data['credentials'].provider_name,
        db_session=request.dbsession
    )
    update_identity = False
    # if current token doesn't match what we have in db - remove old one
    if extng_id and extng_id.access_token != social_data['credentials'].token:
        extng_id.delete()
        update_identity = True

    if not extng_id or update_identity:
        if not update_identity:
            request.session.flash({'msg': 'Your external identity is now '
                                          'connected with your account',
                                   'level': 'warning'})
        ex_identity = ExternalIdentity()
        ex_identity.external_id = social_data['user']['id']
        ex_identity.external_user_name = social_data['user']['user_name']
        ex_identity.provider_name = social_data['credentials'].provider_name
        ex_identity.access_token = social_data['credentials'].token
        ex_identity.token_secret = social_data['credentials'].token_secret
        ex_identity.alt_token = social_data['credentials'].refresh_token
        event.user.external_identities.append(ex_identity)
        request.session.pop('zigg.social_auth', None)


@subscriber(BeforeRender)
def add_globals(event):
    request = event.get('request') or get_current_request()
    flash_messages = request.session.pop_flash()
    event['flash_messages'] = flash_messages
    event['base_url'] = request.registry.settings['base_url']
    request.response.headers[str('x-flash-messages')] = json.dumps(flash_messages)
    # we only need to instantiate the form if user is unlogged
    if hasattr(request, 'user') and not request.user:
        event['layout_login_form'] = UserLoginForm(
            request.POST, context={'request': request})
    else:
        event['layout_login_form'] = None


@subscriber(NewRequest)
def new_request(event):
    environ = event.request.environ
    event.request.response.headers[str('X-Frame-Options')] = str('SAMEORIGIN')
    event.request.response.headers[str('X-XSS-Protection')] = str('1; mode=block')
    if environ['wsgi.url_scheme'] == 'https':
        event.request.response.set_cookie(
            'XSRF-TOKEN', event.request.session.get_csrf_token(), secure=True)
    else:
        event.request.response.set_cookie(
            'XSRF-TOKEN', event.request.session.get_csrf_token())
    if event.request.user:
        event.request.response.headers[str('x-uid')] = str(event.request.user.id)
