# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from authomatic.providers import oauth2, oauth1
from authomatic import Authomatic
from pyramid.security import unauthenticated_userid

from testscaffold.models.user import User
from testscaffold.exceptions import JSONException


def get_user(request):
    userid = unauthenticated_userid(request)
    if userid is not None:
        # this should return None if the user doesn't exist
        # in the database
        return User.by_id(userid, db_session=request.dbsession)


def safe_json_body(request):
    """
    Returns None if json body is missing or erroneous
    """
    try:
        return request.json_body
    except ValueError:
        return None


def unsafe_json_body(request):
    """
    Throws JSONException if json can't deserialize
    """
    try:
        return request.json_body
    except ValueError:
        raise JSONException('Incorrect JSON')


def get_authomatic(request):
    settings = request.registry.settings
    # authomatic social auth
    authomatic_conf = {
        # callback http://yourapp.com/social_auth/twitter
        'twitter': {
            'class_': oauth1.Twitter,
            'consumer_key': settings.get('authomatic.pr.twitter.key', 'X'),
            'consumer_secret': settings.get('authomatic.pr.twitter.secret',
                                            'X'),
        },
        # callback http://yourapp.com/social_auth/facebook
        'facebook': {
            'class_': oauth2.Facebook,
            'consumer_key': settings.get('authomatic.pr.facebook.app_id', 'X'),
            'consumer_secret': settings.get('authomatic.pr.facebook.secret',
                                            'X'),
            'scope': ['email'],
        },
        # callback http://yourapp.com/social_auth/google
        'google': {
            'class_': oauth2.Google,
            'consumer_key': settings.get('authomatic.pr.google.key', 'X'),
            'consumer_secret': settings.get(
                'authomatic.pr.google.secret', 'X'),
            'scope': ['email'],
        }
    }
    return Authomatic(config=authomatic_conf,
                      secret=settings['authomatic.secret'])
