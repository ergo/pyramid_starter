# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pytest

from six.moves.urllib import parse

from testscaffold.tests.utils import (
    create_entry,
    session_context,
    create_admin,
    create_user,
)


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIResources(object):

    def test_user_permission_wrong_resurce(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            entry = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                 sqla_session=session)

        node_id = entry.resource_id
        url_path = '/api/0.1/resources/{}/user_permissions'.format(-55)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'user_id': user.id,
            'perm_name': 'blabla'
        }
        response = full_app.post_json(
            url_path, perm_dict, status=404, headers=headers)

    def test_user_permission_add_wrong(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            entry = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                 sqla_session=session)

        node_id = entry.resource_id
        url_path = '/api/0.1/resources/{}/user_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'user_id': user.id,
            'perm_name': 'blabla'
        }
        response = full_app.post_json(
            url_path, perm_dict, status=200, headers=headers)

    def test_user_permission_add_proper(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user(
                {'user_name': 'aaaa', 'email': 'foo'}, sqla_session=session)
            entry = create_entry(
                {'resource_name': 'entry-x', 'note': 'x'}, sqla_session=session)

        node_id = entry.resource_id
        url_path = '/api/0.1/resources/{}/user_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'user_id': user.id,
            'perm_name': 'editor'
        }
        response = full_app.post_json(url_path, perm_dict, status=200,
                                      headers=headers)
        assert response.json['user_id'] == user.id
        assert response.json['perm_name'] == 'editor'
        assert response.json['resource_id'] == node_id

    def test_user_permission_remove_wrong(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            entry = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                 sqla_session=session)

        node_id = entry.resource_id
        qs = parse.urlencode({'user_id': user.id, 'perm_name': 'BLABLA'})
        url_path = '/api/0.1/resources/{}/user_permissions?{}'.format(
            node_id, qs)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.delete(url_path, status=200, headers=headers)
