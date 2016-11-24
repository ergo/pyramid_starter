# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import mock
import pytest
from pyramid import testing

from testscaffold.tests.utils import session_context


def dummy_request(dbsession):
    from webob.multidict import MultiDict
    from pyramid.request import apply_request_extensions

    req = testing.DummyRequest(base_url='http://testscaffold.com',
                               dbsession=dbsession)
    req.route_url = mock.Mock(return_value='/')
    req.POST = MultiDict()
    req.GET = MultiDict()
    req.params = MultiDict()
    req.session = mock.Mock()
    apply_request_extensions(req)
    return req


@pytest.mark.usefixtures('with_migrations', 'clean_tables', 'minimal_setup')
class TestFixtureCleanup(object):
    def test_cleanup(self, sqla_session):
        from testscaffold.models.user import User
        with session_context(sqla_session) as session:
            user = User(id=1, email='foasfsfao', user_name='barafsf')
            user.persist(flush=True, db_session=session)
