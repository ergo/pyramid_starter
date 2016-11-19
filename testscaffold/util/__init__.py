# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from pyramid.httpexceptions import HTTPBadRequest


def safe_integer(integer):
    try:
        return int(integer)
    except (ValueError, TypeError):
        raise HTTPBadRequest()


def session_provider(request):
    """ provides sqlalchemy session for ziggurat_foundations """
    return request.dbsession
