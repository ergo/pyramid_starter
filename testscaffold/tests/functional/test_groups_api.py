# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from six.moves.urllib import parse

import pytest

from testscaffold.tests.utils import create_group, session_context, create_admin


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIGroups(object):
    def test_groups_list(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_group({'group_name': 'test', 'description': 'foo'},
                         sqla_session=session)
            create_group({'group_name': 'test2', 'description': 'foo2'},
                         sqla_session=session)

        url_path = '/api/0.1/groups'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json
        assert len(items) == 2

    def test_group_create_no_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/groups'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.post_json(url_path, status=422, headers=headers)

    def test_group_create_bad_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/groups'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        group_dict = {'xxx': 'yyy'}
        response = full_app.post_json(url_path, group_dict, status=422,
                                      headers=headers)
        required = ['group_name']
        assert sorted(required) == sorted(response.json.keys())

    def test_group_create(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = '/api/0.1/groups'
        headers = {str('x-testscaffold-auth-token'): str(token)}
        group_dict = {
            'id': -9999,
            'group_name': 'some-new_group',
            'description': 'description'
        }
        response = full_app.post_json(url_path, group_dict, status=200,
                                      headers=headers)
        assert response.json['id'] > 0
        assert group_dict['group_name'] == response.json['group_name']
        assert group_dict['description'] == response.json['description']

    def test_group_patch(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group(
                {'group_name': 'testX', 'description': 'testX'},
                sqla_session=session)

        url_path = '/api/0.1/groups/{}'.format(group.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        group_dict = {
            'id': -9,
            'group_name': 'some-new_groupCHANGED',
            'description': 'changed'
        }
        response = full_app.patch_json(url_path, group_dict, status=200,
                                       headers=headers)
        assert response.json['id'] == group.id
        assert group_dict['group_name'] == response.json['group_name']
        assert group_dict['description'] == response.json['description']

    def test_group_delete(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'testX'}, sqla_session=session)
        url_path = '/api/0.1/groups/{}'.format(group.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIGroupsPermissions(object):
    def test_permission_add(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'test'}, sqla_session=session)

        url_path = '/api/0.1/groups/{}/permissions'.format(group.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        permission = {
            'permission': 'root_administration',
        }
        assert not group.permissions
        full_app.post_json(url_path, permission, status=200, headers=headers)
        sqla_session.expire_all()
        assert group.permissions[0].perm_name == 'root_administration'

    def test_permission_delete_not_found(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group(
                {'group_name': 'test'},
                permissions=['root_administration', 'dummy_permission'],
                sqla_session=session)

        url_path = '/api/0.1/groups/{}/permissions'.format(group.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        permission = {
            'permission': 'c',
        }
        full_app.delete(url_path, permission, status=404, headers=headers)

    def test_permission_delete(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group(
                {'group_name': 'test'},
                permissions=['root_administration', 'dummy_permission'],
                sqla_session=session)

        url_path = '/api/0.1/groups/{}/permissions'.format(group.id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        permission = {
            'permission': 'root_administration',
        }
        qs = parse.urlencode(permission)
        full_app.delete('{}?{}'.format(url_path, qs),
                        params=permission, status=200, headers=headers)
        sqla_session.expire_all()
        assert group.permissions[0].perm_name == 'dummy_permission'
