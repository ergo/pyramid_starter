# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest

from testscaffold.tests.utils import create_user, session_context


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIUsers(object):
    def test_wrong_token(self, full_app):
        url_path = '/api/0.1/users'
        headers = {str('x-testscaffold-auth-token'): str('test')}
        full_app.post(url_path, {}, status=403, headers=headers)

    def test_list_users(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            create_user({'user_name': 'test2', 'email': 'test@test.local2'},
                        sqla_session=session)
            token = admin.auth_tokens[0].token

        url_path = '/api/0.1/users'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json
        assert len(items) == 2

    def test_create_user_no_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            token = admin.auth_tokens[0].token

        url_path = '/api/0.1/users'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.post_json(url_path, status=422, headers=headers)

    def test_create_user_bad_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            token = admin.auth_tokens[0].token

        url_path = '/api/0.1/users'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        user_dict = {'xxx': 'yyy'}
        response = full_app.post_json(url_path, user_dict, status=422,
                                      headers=headers)
        required = ['user_name', 'email', 'password']
        assert sorted(required) == sorted(response.json.keys())

    def test_create_user(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            token = admin.auth_tokens[0].token

        url_path = '/api/0.1/users'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        user_dict = {
            'id': -9999,
            'user_name': 'some-new_user',
            'password': 'new_password',
            'email': 'email@foo.bar'
        }
        response = full_app.post_json(url_path, user_dict, status=200,
                                      headers=headers)
        assert response.json['id'] > 0
        assert user_dict['user_name'] == response.json['user_name']
        assert user_dict['email'] == response.json['email']
        assert 'last_login_date' in response.json
        assert 'registered_date' in response.json
        assert response.json['status'] == 1

    def test_patch_user(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            token = admin.auth_tokens[0].token
            user = create_user(
                {'user_name': 'testX', 'email': 'testX@test.local'},
                sqla_session=session)

        url_path = '/api/0.1/users/{}'.format(user.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        user_dict = {
            'id': -9,
            'user_name': 'some-new_userCHANGED',
            'email': 'email@fooCHANGED.bar'
        }
        response = full_app.patch_json(url_path, user_dict, status=200,
                                       headers=headers)
        assert response.json['id'] == user.id
        assert user_dict['user_name'] == response.json['user_name']
        assert user_dict['email'] == response.json['email']

    def test_delete_user(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin = create_user(
                {'user_name': 'test', 'email': 'test@test.local'},
                permissions=['root_administration'],
                sqla_session=session)
            token = admin.auth_tokens[0].token
            user = create_user(
                {'user_name': 'testX', 'email': 'testX@test.local'},
                sqla_session=session)
        url_path = '/api/0.1/users/{}'.format(user.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)
