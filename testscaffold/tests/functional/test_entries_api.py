# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest

from six.moves.urllib import parse

from testscaffold.tests.utils import (
    create_entry,
    session_context,
    create_admin)


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIEntries(object):
    def test_wrong_token(self, full_app):
        url_path = '/api/0.1/entries'
        headers = {str('x-testscaffold-auth-token'): str('test')}
        full_app.post(url_path, {}, status=403, headers=headers)

    def test_entries_list(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            for x in range(1, 51):
                create_entry({'resource_name': 'entry-x{}'.format(x),
                              'note': 'x{}'.format(x)},
                             sqla_session=session)
                create_entry({'resource_name': 'entry-y{}'.format(x),
                              'note': 'y{}'.format(x)},
                             sqla_session=session)

        url_path = '/api/0.1/entries'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json

        assert len(items) == 50
        assert items[0]['resource_name'] == 'entry-x1'
        assert items[49]['resource_name'] == 'entry-y25'
        assert response.headers['x-pages'] == '2'
        assert response.headers['x-current-page'] == '1'
        assert response.headers['x-total-count'] == '100'

    def test_entry_create_no_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/entries'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.post_json(url_path, status=422, headers=headers)

    @pytest.mark.parametrize("test_input, error_keys", [
        ({}, ['resource_name']),
        ({'parent_id': 'v'}, ['resource_name', 'parent_id']),
        ({'ordering': 5, 'resource_name': 'x'}, ['_schema', ]),
        ({'parent_id': 5}, ['resource_name', 'parent_id']),
    ])
    def test_entry_create_bad_json(self, full_app, sqla_session,
                                   test_input, error_keys):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/entries'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.post_json(url_path, test_input, status=422,
                                      headers=headers)
        assert sorted(error_keys) == sorted(response.json.keys())

    def test_entry_create(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/entries'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'id': -9999,
            'resource_name': 'some-new-entry',
            'note': 'text'
        }
        response = full_app.post_json(url_path, entry_dict, status=200,
                                      headers=headers)
        assert response.json['resource_id'] > 0
        assert response.json['ordering'] == 1
        assert entry_dict['resource_name'] == response.json['resource_name']
        assert entry_dict['note'] == response.json['note']

    def test_entry_patch(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            entry = create_entry({'resource_name': 'entry-x',
                                  'note': 'x'},
                                 sqla_session=session)

        url_path = '/api/0.1/entries/{}'.format(entry.resource_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'resource_id': -9,
            'resource_name': 'CHANGED',
            'note': 'CHANGED'
        }
        response = full_app.patch_json(url_path, entry_dict, status=200,
                                       headers=headers)
        assert response.json['resource_id'] == entry.resource_id
        assert entry_dict['resource_name'] == response.json['resource_name']
        assert entry_dict['note'] == response.json['note']

    def test_entry_delete(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            entry = create_entry({'resource_name': 'entry-x',
                                  'note': 'x'},
                                 sqla_session=session)
        url_path = '/api/0.1/entries/{}'.format(entry.resource_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)
