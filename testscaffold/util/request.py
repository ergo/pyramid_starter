# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import copy

from authomatic import Authomatic
from authomatic.providers import oauth2, oauth1
from pyramid.security import unauthenticated_userid

from testscaffold.exceptions import JSONException
from testscaffold.services.user import UserService


def get_user(request):
    userid = unauthenticated_userid(request)
    if userid is not None:
        # this should return None if the user doesn't exist
        # in the database
        return UserService.get(userid, db_session=request.dbsession)


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
        raise JSONException("Incorrect JSON")


def get_authomatic(request):
    settings = request.registry.settings
    # authomatic social auth
    authomatic_conf = {
        # callback http://yourapp.com/social_auth/twitter
        "twitter": {
            "class_": oauth1.Twitter,
            "consumer_key": settings.get("authomatic.pr.twitter.key", "X"),
            "consumer_secret": settings.get("authomatic.pr.twitter.secret", "X"),
        },
        # callback http://yourapp.com/social_auth/facebook
        "facebook": {
            "class_": oauth2.Facebook,
            "consumer_key": settings.get("authomatic.pr.facebook.app_id", "X"),
            "consumer_secret": settings.get("authomatic.pr.facebook.secret", "X"),
            "scope": ["email"],
        },
        # callback http://yourapp.com/social_auth/google
        "google": {
            "class_": oauth2.Google,
            "consumer_key": settings.get("authomatic.pr.google.key", "X"),
            "consumer_secret": settings.get("authomatic.pr.google.secret", "X"),
            "scope": ["email"],
        },
    }
    return Authomatic(config=authomatic_conf, secret=settings["authomatic.secret"])


def gen_pagination_headers(request, paginator):
    """
    Generate pagination headers from paginator
    :param request:
    :param paginator:
    :return:
    """
    headers = {
        "x-total-count": str(paginator.item_count),
        "x-current-page": str(paginator.page),
        "x-items-per-page": str(paginator.items_per_page),
        "x-pages": str(paginator.page_count),
    }
    params_dict = request.GET.dict_of_lists()
    last_page_params = copy.deepcopy(params_dict)
    last_page_params["page"] = paginator.last_page or 1
    first_page_params = copy.deepcopy(params_dict)
    first_page_params.pop("page", None)
    next_page_params = copy.deepcopy(params_dict)
    next_page_params["page"] = paginator.next_page or paginator.last_page or 1
    prev_page_params = copy.deepcopy(params_dict)
    prev_page_params["page"] = paginator.previous_page or 1
    lp_url = request.current_route_url(_query=last_page_params)
    fp_url = request.current_route_url(_query=first_page_params)
    links = ['rel="last", <{}>'.format(lp_url), 'rel="first", <{}>'.format(fp_url)]
    if first_page_params != prev_page_params:
        prev_url = request.current_route_url(_query=prev_page_params)
        links.append('rel="prev", <{}>'.format(prev_url))
    if last_page_params != next_page_params:
        next_url = request.current_route_url(_query=next_page_params)
        links.append('rel="next", <{}>'.format(next_url))
    headers["link"] = "; ".join(links)
    return headers
