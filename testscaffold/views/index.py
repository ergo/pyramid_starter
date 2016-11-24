# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import uuid
from datetime import datetime, timedelta

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED, remember
from pyramid.view import view_config

from testscaffold.events import EmailEvent, SocialAuthEvent
from testscaffold.models.user import User
from testscaffold.validation.forms import (UserCreateForm,
                                           UserLoginForm,
                                           UserLostPasswordForm,
                                           UserNewPasswordForm)
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory('testscaffold')


class IndexViews(BaseView):
    @view_config(route_name='/', renderer='testscaffold:templates/index.jinja2',
                 permission=NO_PERMISSION_REQUIRED)
    def index(self):
        request = self.request
        login_form = UserLoginForm(request.POST, context={'request': request})
        log.warning('index', extra={'foo': 'xxx'})
        log.info('locale', extra={'locale': request.locale_name})
        return {'login_form': login_form}

    @view_config(
        route_name='objects',
        renderer='testscaffold:templates/admin/relation_remove.jinja2',
        match_param=('object=error'),
        request_method='GET')
    def error_test(self):
        return 1 / 0

    @view_config(route_name='lost_password',
                 renderer='testscaffold:templates/auth/lost_password.jinja2',
                 permission=NO_PERMISSION_REQUIRED)
    def lost_password(self):
        """
        Presents lost password page - sends password reset link to
        specified email address.
        This link is valid only for 10 minutes
        """
        request = self.request
        form = UserLostPasswordForm(request.POST, context={'request': request})
        if request.method == 'POST' and form.validate():
            user = User.by_email(form.email.data, db_session=request.dbsession)
            if user:
                user.regenerate_security_code()
                user.security_code_date = datetime.utcnow()
                title = self.translate(
                    _('${project} :: New password request', mapping={
                        'project': 'testscaffold'
                    }))
                email_vars = {'user': user,
                              'request': request,
                              'email_title': title}

                ev = EmailEvent(
                    request, recipients=[user.email], tmpl_vars=email_vars,
                    tmpl_loc='testscaffold:templates/emails/lost_password.jinja2')
                request.registry.notify(ev)
                msg = {'msg': self.translate(
                    _('Password reset email had been sent. '
                      'Please check your mailbox for further instructions.'
                      'If you can\'t see the message please check '
                      'your spam box.')),
                    'level': 'success'}
                request.session.flash(msg)
                return HTTPFound(location=request.route_url('lost_password'))
            else:
                msg = {'msg': 'Email not found', 'level': 'warning'}
                request.session.flash(msg)
        return {"lost_password_form": form}

    @view_config(route_name='lost_password_generate',
                 permission=NO_PERMISSION_REQUIRED,
                 renderer='testscaffold:templates/auth/'
                          'lost_password_generate.jinja2')
    def lost_password_generate(self):
        """
        Shows new password form - perform time check and set new password for user
        """
        request = self.request
        user = User.by_user_name_and_security_code(
            request.params.get('user_name'),
            request.params.get(
                'security_code'),
            db_session=request.dbsession)
        delta = 0
        if user:
            delta = datetime.utcnow() - user.security_code_date

        if user and delta.total_seconds() < 600:
            form = UserNewPasswordForm(request.POST,
                                       context={'context': request})
            if request.method == "POST" and form.validate():
                user.set_password(form.password.data)
                msg = {'msg': self.translate(
                    _('You can sign in with your new password.')),
                    'level': 'success'}
                request.session.flash(msg)
                return HTTPFound(location=request.route_url('register'))
            else:
                return {"update_password_form": form}
        else:
            return Response('Security code expired')

    @view_config(route_name='register', renderer='json',
                 permission=NO_PERMISSION_REQUIRED, xhr=True)
    @view_config(route_name='register',
                 renderer='testscaffold:templates/auth/register.jinja2',
                 permission=NO_PERMISSION_REQUIRED)
    def register(self):
        """
        Render register page with form
        Also handles oAuth flow for registration
        """
        request = self.request
        login_url = request.route_url('ziggurat.routes.sign_in')

        login_form = UserLoginForm(request.POST, context={'request': request})
        # some logic to handle came_from variable that we can use
        # to redirect user that tried to access forbidden resource
        if request.query_string:
            query_string = '?%s' % request.query_string
        else:
            query_string = ''
        referrer = '%s%s' % (request.path, query_string)

        for url in [login_url, '/register']:
            if url in referrer:
                # never use the login form itself as came_from
                # or we may end up with a redirect loop
                referrer = '/'
                break

        registration_form = UserCreateForm(request.POST,
                                           context={'request': request})

        # populate form from oAuth session data returned by velruse
        social_data = request.session.get('zigg.social_auth')
        if request.method != 'POST' and social_data:
            log.info('social_auth', extra={'social_data': social_data})
            form_data = {'email': social_data['user'].get('email')}
            form_data['user_password'] = str(uuid.uuid4())
            # repopulate form this time from oauth data
            registration_form = UserCreateForm(context={'request': request},
                                               **form_data)

        if request.method == "POST" and registration_form.validate():
            # insert new user here
            new_user = User()
            registration_form.populate_obj(new_user)
            new_user.persist(flush=True, db_session=request.dbsession)
            new_user.regenerate_security_code()
            new_user.status = 1
            new_user.set_password(new_user.password)
            new_user.registration_ip = request.environ.get('REMOTE_ADDR')
            log.info('register', extra={'new_user': new_user.user_name})

            # bind 3rd party identity
            if social_data:
                request.registry.notify(SocialAuthEvent(request, new_user,
                                                        social_data))

            title = _("${project} :: Start information",
                      mapping={'project': 'testscaffold'})
            email_vars = {'user': new_user,
                          'email_title': self.translate(title)}
            ev = EmailEvent(request,
                            recipients=[new_user.email], tmpl_vars=email_vars,
                            tmpl_loc='testscaffold:'
                                     'templates/emails/registered.jinja2')
            request.registry.notify(ev)
            request.session.flash(
                {'msg': self.translate(_('You have successfully registered.')),
                 'level': 'success'})
            headers = remember(request, new_user.id)
            return HTTPFound(location=request.route_url('/'),
                             headers=headers)
        return {
            "registration_form": registration_form,
            'login_form': login_form
        }

    @view_config(route_name='language', renderer='json',
                 permission=NO_PERMISSION_REQUIRED)
    def set_language_cookie(self):
        request = self.request
        selected_language = request.matchdict.get('language', 'en')
        came_from = request.params.get('came_from', '/')
        resp = HTTPFound(location=request.route_url('/'))
        request.response.set_cookie(
            '_LOCALE_', selected_language, max_age=timedelta(days=365))
        return request.response.merge_cookies(resp)
