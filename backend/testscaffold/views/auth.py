# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from datetime import datetime

from authomatic.adapters import WebObAdapter
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import NO_PERMISSION_REQUIRED, remember
from pyramid.view import view_config
from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInBadAuth
from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInSuccess
from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignOut
from testscaffold.services.external_identity import ExternalIdentityService

from testscaffold.events import SocialAuthEvent
from testscaffold.views import BaseView

log = logging.getLogger(__name__)

_ = TranslationStringFactory("testscaffold")


class AuthView(BaseView):
    @view_config(context=ZigguratSignInSuccess, permission=NO_PERMISSION_REQUIRED)
    def sign_in(self):
        request = self.request
        user = request.context.user
        user.last_login_date = datetime.utcnow()
        return self.shared_sign_in(
            user, request.context.headers, request.context.came_from
        )

    @view_config(context=ZigguratSignInBadAuth, permission=NO_PERMISSION_REQUIRED)
    def bad_auth(self):
        request = self.request
        log.info("bad_auth", {"user": None})
        # action like a warning flash message on bad logon
        msg = {
            "msg": self.translate(_("Wrong username or password")),
            "level": "danger",
        }
        request.session.flash(msg)
        return HTTPFound(
            location=request.route_url("register"), headers=request.context.headers
        )

    @view_config(context=ZigguratSignOut, permission=NO_PERMISSION_REQUIRED)
    def sign_out(self):
        request = self.request
        request.session.flash(
            {"msg": self.translate(_("Signed out")), "level": "success"}
        )
        return HTTPFound(
            location=request.route_url("/"), headers=request.context.headers
        )

    @view_config(route_name="social_auth", permission=NO_PERMISSION_REQUIRED)
    def social_auth(self):
        request = self.request
        # Get the internal provider name URL variable.
        provider_name = request.matchdict.get("provider")

        # Start the login procedure.
        adapter = WebObAdapter(request, request.response)
        result = request.authomatic.login(adapter, provider_name)
        if result:
            if result.error:
                return self.handle_auth_error(result)
            elif result.user:
                return self.handle_auth_success(result)
        return request.response

    def handle_auth_error(self, result):
        request = self.request
        # Login procedure finished with an error.
        request.session.pop("zigg.social_auth", None)
        log.error("social_auth", extra={"error": result.error.message})
        msg = {
            "msg": self.translate(
                _(
                    "Something went wrong when accessing third party "
                    "provider - please try again"
                )
            ),
            "level": "danger",
        }
        request.session.flash(msg)
        return HTTPFound(location=request.route_url("/"))

    def handle_auth_success(self, result):
        request = self.request
        # Hooray, we have the user!
        # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
        # We need to update the user to get more info.
        if result.user:
            result.user.update()
        social_data = {
            "user": {"data": result.user.data},
            "credentials": result.user.credentials,
        }
        # normalize data
        social_data["user"]["id"] = result.user.id
        user_name = result.user.username or ""
        # use email name as username for google
        if social_data["credentials"].provider_name == "google" and result.user.email:
            user_name = result.user.email
        social_data["user"]["user_name"] = user_name
        social_data["user"]["email"] = result.user.email or ""

        request.session["zigg.social_auth"] = social_data
        # user is logged so bind his external identity with account
        if request.user:
            log.info("social_auth", extra={"user_found": True})
            request.registry.notify(SocialAuthEvent(request, request.user, social_data))
            request.session.pop("zigg.social_auth", None)
            return HTTPFound(location=request.route_url("/"))
        else:
            log.info("social_auth", extra={"user_found": False})

            user = ExternalIdentityService.user_by_external_id_and_provider(
                social_data["user"]["id"],
                social_data["credentials"].provider_name,
                db_session=request.dbsession,
            )
            # user tokens are already found in our db
            if user:
                request.registry.notify(SocialAuthEvent(request, user, social_data))
                headers = remember(request, user.id)
                request.session.pop("zigg.social_auth", None)
                return self.shared_sign_in(user, headers)
            else:
                msg = {
                    "msg": self.translate(
                        _(
                            "You need to finish registration "
                            "process to bind your external "
                            "identity to your account or sign in to "
                            "existing account"
                        )
                    ),
                    "level": "warning",
                }
                request.session.flash(msg)
                return HTTPFound(location=request.route_url("register"))

    def shared_sign_in(self, user, headers, came_from=None):
        """ Shared among sign_in and social_auth views"""
        request = self.request
        # actions performed on sucessful logon, flash message/new csrf token
        # user status validation etc.
        if came_from is None:
            came_from = request.route_url("/")

        log.info("shared_sign_in", extra={"user": user})
        request.session.flash(
            {"msg": self.translate(_("Signed in")), "level": "success"}
        )
        # if social data is still present bind the account
        social_data = request.session.get("zigg.social_auth")
        if social_data:
            request.registry.notify(SocialAuthEvent(request, user, social_data))
            request.session.pop("zigg.social_auth", None)
        return HTTPFound(location=came_from, headers=headers)
