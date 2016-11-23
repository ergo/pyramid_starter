# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pytest

from six.moves.urllib import parse

from testscaffold.tests.utils import (
    create_entry,
    session_context,
    create_admin,
    create_user,
    create_group,
)

from testscaffold.models.user_resource_permission import UserResourcePermission
from testscaffold.models.group_resource_permission import GroupResourcePermission
from ziggurat_foundations.models.services.user_resource_permission import \
    UserResourcePermissionService
from ziggurat_foundations.models.services.group_resource_permission import \
    GroupResourcePermissionService


@pytest.mark.usefixtures('full_app', 'with_migrations', 'clean_tables',
                         'sqla_session')
class TestFunctionalAPIResources(object):
    def test_user_permission_wrong_resource(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
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
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
        url_path = '/api/0.1/resources/{}/user_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'user_id': -9,
            'perm_name': 'blabla'
        }
        response = full_app.post_json(
            url_path, perm_dict, status=422, headers=headers)
        assert 'perm_name' in response.json
        assert 'user_id' in response.json

    def test_user_permission_add_proper(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user(
                {'user_name': 'aaaa', 'email': 'foo'}, sqla_session=session)
            resource = create_entry(
                {'resource_name': 'entry-x', 'note': 'x'}, sqla_session=session)

        node_id = resource.resource_id
        url_path = '/api/0.1/resources/{}/user_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_name = 'editor'
        perm_dict = {
            'user_id': user.id,
            'perm_name': perm_name
        }
        response = full_app.post_json(url_path, perm_dict, status=200,
                                      headers=headers)
        assert response.json['user_id'] == user.id
        assert response.json['perm_name'] == perm_name
        assert response.json['resource_id'] == node_id
        perm_inst = UserResourcePermissionService.get(
            user.id, resource_id=node_id, perm_name=perm_name,
            db_session=sqla_session)
        assert isinstance(perm_inst, UserResourcePermission)

    def test_user_permission_remove_wrong(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
        qs = parse.urlencode({'user_id': -99, 'perm_name': 'BLABLA'})
        url_path = '/api/0.1/resources/{}/user_permissions?{}'.format(
            node_id, qs)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.delete(url_path, status=422, headers=headers)
        assert 'perm_name' in response.json
        assert 'user_id' in response.json

    def test_user_permission_remove_proper(self, full_app, sqla_session):
        perm_name = 'editor'
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({'user_name': 'aaaa', 'email': 'foo'},
                               sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)
            perm_inst = UserResourcePermission(
                user_id=user.id, perm_name=perm_name)
            resource.user_permissions.append(perm_inst)

        node_id = resource.resource_id
        qs = parse.urlencode({'user_id': user.id, 'perm_name': perm_name})
        url_path = '/api/0.1/resources/{}/user_permissions?{}'.format(
            node_id, qs)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.delete(url_path, status=200, headers=headers)
        perm_inst = UserResourcePermissionService.get(
            user.id, resource_id=node_id, perm_name=perm_name,
            db_session=sqla_session)
        assert not isinstance(perm_inst, UserResourcePermission)

    def test_group_permission_wrong_resource(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'aaaa'}, sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
        url_path = '/api/0.1/resources/{}/group_permissions'.format(-55)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'group_id': group.id,
            'perm_name': 'blabla'
        }
        response = full_app.post_json(
            url_path, perm_dict, status=404, headers=headers)

    def test_group_permission_add_wrong(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'aaaa'}, sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
        url_path = '/api/0.1/resources/{}/group_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_dict = {
            'group_id': -9,
            'perm_name': 'blabla'
        }
        response = full_app.post_json(
            url_path, perm_dict, status=422, headers=headers)
        assert 'perm_name' in response.json
        assert 'group_id' in response.json

    def test_group_permission_add_proper(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'aaaa'}, sqla_session=session)
            resource = create_entry(
                {'resource_name': 'entry-x', 'note': 'x'}, sqla_session=session)

        node_id = resource.resource_id
        url_path = '/api/0.1/resources/{}/group_permissions'.format(node_id)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        perm_name = 'editor'
        perm_dict = {
            'group_id': group.id,
            'perm_name': perm_name
        }
        response = full_app.post_json(url_path, perm_dict, status=200,
                                      headers=headers)
        assert response.json['group_id'] == group.id
        assert response.json['perm_name'] == perm_name
        assert response.json['resource_id'] == node_id
        perm_inst = GroupResourcePermissionService.get(
            group.id, resource_id=node_id, perm_name=perm_name,
            db_session=sqla_session)
        assert isinstance(perm_inst, GroupResourcePermission)

    def test_group_permission_remove_wrong(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'aaaa'}, sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)

        node_id = resource.resource_id
        qs = parse.urlencode({'user_id': -99, 'perm_name': 'BLABLA'})
        url_path = '/api/0.1/resources/{}/group_permissions?{}'.format(
            node_id, qs)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.delete(url_path, status=422, headers=headers)
        assert 'perm_name' in response.json
        assert 'group_id' in response.json

    def test_group_permission_remove_proper(self, full_app, sqla_session):
        perm_name = 'editor'
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            group = create_group({'group_name': 'aaaa'}, sqla_session=session)
            resource = create_entry({'resource_name': 'entry-x', 'note': 'x'},
                                    sqla_session=session)
            perm_inst = GroupResourcePermission(
                group_id=group.id, perm_name=perm_name)
            resource.group_permissions.append(perm_inst)

        node_id = resource.resource_id
        qs = parse.urlencode({'group_id': group.id, 'perm_name': perm_name})
        url_path = '/api/0.1/resources/{}/group_permissions?{}'.format(
            node_id, qs)
        headers = {str('x-testscaffold-auth-token'): str(token)}
        response = full_app.delete(url_path, status=200, headers=headers)
        perm_inst = GroupResourcePermissionService.get(
            group.id, resource_id=node_id, perm_name=perm_name,
            db_session=sqla_session)
        assert not isinstance(perm_inst, GroupResourcePermission)
