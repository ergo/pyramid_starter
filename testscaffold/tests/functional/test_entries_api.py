# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import pprint

import pytest

from six.moves.urllib import parse

from testscaffold.tests.utils import (
    create_entry,
    session_context,
    create_admin)


def create_default_tree(db_session):
    root = create_entry(
        {'resource_id': -1, 'resource_name': 'root a',
         'ordering': 1}, sqla_session=db_session)
    res_a = create_entry({'resource_id': 1, 'resource_name': 'a', 'ordering': 1,
                          'parent_id': root.resource_id},
                         sqla_session=db_session)
    res_aa = create_entry(
        {'resource_id': 5, 'resource_name': 'aa', 'ordering': 1,
         'parent_id': res_a.resource_id}, sqla_session=db_session)
    res_ab = create_entry(
        {'resource_id': 6, 'resource_name': 'ab', 'ordering': 2,
         'parent_id': res_a.resource_id},
        sqla_session=db_session)
    res_ac = create_entry(
        {'resource_id': 7, 'resource_name': 'ac', 'ordering': 3,
         'parent_id': res_a.resource_id},
        sqla_session=db_session)
    res_aca = create_entry(
        {'resource_id': 9, 'resource_name': 'aca', 'ordering': 1,
         'parent_id': res_ac.resource_id},
        sqla_session=db_session)
    res_acaa = create_entry(
        {'resource_id': 12, 'resource_name': 'aca', 'ordering': 1,
         'parent_id': res_aca.resource_id},
        sqla_session=db_session)
    res_ad = create_entry(
        {'resource_id': 8, 'resource_name': 'ad', 'ordering': 4,
         'parent_id': res_a.resource_id},
        sqla_session=db_session)
    res_b = create_entry({'resource_id': 2, 'resource_name': 'b', 'ordering': 2,
                          'parent_id': root.resource_id},
                         sqla_session=db_session)
    res_ba = create_entry(
        {'resource_id': 4, 'resource_name': 'ba', 'ordering': 1,
         'parent_id': res_b.resource_id},
        sqla_session=db_session)
    res_c = create_entry({'resource_id': 3, 'resource_name': 'c', 'ordering': 3,
                          'parent_id': root.resource_id},
                         sqla_session=db_session)
    res_d = create_entry(
        {'resource_id': 10, 'resource_name': 'd', 'ordering': 4,
         'parent_id': root.resource_id},
        sqla_session=db_session)
    res_e = create_entry(
        {'resource_id': 11, 'resource_name': 'e', 'ordering': 5,
         'parent_id': root.resource_id},
        sqla_session=db_session)
    root_b = create_entry(
        {'resource_id': -2, 'resource_name': 'root b', 'ordering': 2},
        sqla_session=db_session)
    root_c = create_entry(
        {'resource_id': -3, 'resource_name': 'root 3', 'ordering': 3},
        sqla_session=db_session)
    return [root, root_b, root_c]


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
            'note': 'text',
            'ordering': 1
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

    def test_root_nesting(self, full_app, sqla_session):
        from ziggurat_foundations.models.services.resource import \
            ResourceService
        root = create_default_tree(sqla_session)[0]

        result = ResourceService.from_resource_deeper(root.resource_id,
                                                      db_session=sqla_session)
        tree_struct = ResourceService.build_subtree_strut(result)['children'][
            -1]
        pprint.pprint(tree_struct)
        assert tree_struct['node'].resource_id == -1
        l1_nodes = [n for n in tree_struct['children'].values()]
        a_node = tree_struct['children'][1];
        b_node = tree_struct['children'][2];
        ac_node = a_node['children'][7]
        l_a_nodes = [n for n in a_node['children'].values()]
        l_b_nodes = [n for n in b_node['children'].values()]
        l_ac_nodes = [n for n in ac_node['children'].values()]
        assert [n['node'].resource_id for n in l1_nodes] == [1, 2, 3, 10, 11]
        assert [n['node'].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert [n['node'].resource_id for n in l_b_nodes] == [4]
        assert [n['node'].resource_id for n in l_ac_nodes] == [9]

    def test_entry_no_parent_middle(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = '/api/0.1/entries'

        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'id': -9999,
            'resource_name': 'some-new-entry',
            'note': 'text',
            'ordering': 2
        }
        response = full_app.post_json(url_path, entry_dict, status=200,
                                      headers=headers)
        from ziggurat_foundations.models.services.resource import \
            ResourceService
        result = ResourceService.from_parent_deeper(
            None, db_session=sqla_session, limit_depth=1)
        tree_struct = ResourceService.build_subtree_strut(result)['children']
        pprint.pprint(tree_struct)

        assert response.json['resource_id'] > 0
        assert response.json['ordering'] == 2

    def test_entry_no_parent_last(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = '/api/0.1/entries'

        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'id': -9999,
            'resource_name': 'some-new-entry',
            'note': 'text',
            'ordering': 4
        }
        response = full_app.post_json(url_path, entry_dict, status=200,
                                      headers=headers)
        assert response.json['resource_id'] > 0
        assert response.json['ordering'] == 4

    def test_entry_no_parent_too_high(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = '/api/0.1/entries'

        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'id': -9999,
            'resource_name': 'some-new-entry',
            'note': 'text',
            'ordering': 5
        }
        response = full_app.post_json(url_path, entry_dict, status=422,
                                      headers=headers)
        assert '4' in response.json['_schema'][0]

    def test_entry_no_parent_too_low(self, full_app, sqla_session):
        from ziggurat_foundations.models.services.resource import \
            ResourceService
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = '/api/0.1/entries'

        headers = {str('x-testscaffold-auth-token'): str(token)}
        entry_dict = {
            'id': -9999,
            'resource_name': 'some-new-entry',
            'note': 'text',
            'ordering': -5
        }
        result = ResourceService.from_parent_deeper(
            None, db_session=sqla_session)
        tree_struct = ResourceService.build_subtree_strut(result)['children']
        pprint.pprint(tree_struct)

        response = full_app.post_json(url_path, entry_dict, status=422,
                                      headers=headers)
        pprint.pprint(response.json)
        assert '1' in response.json['_schema'][0]
