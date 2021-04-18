import pprint

import pytest

from testscaffold.tests.utils import create_entry, session_context, create_admin


def create_default_tree(db_session):
    root = create_entry(
        {"resource_id": -1, "resource_name": "root a", "ordering": 1},
        sqla_session=db_session,
    )
    res_a = create_entry(
        {
            "resource_id": 1,
            "resource_name": "a",
            "ordering": 1,
            "parent_id": root.resource_id,
        },
        sqla_session=db_session,
    )
    res_aa = create_entry(
        {
            "resource_id": 5,
            "resource_name": "aa",
            "ordering": 1,
            "parent_id": res_a.resource_id,
        },
        sqla_session=db_session,
    )
    res_ab = create_entry(
        {
            "resource_id": 6,
            "resource_name": "ab",
            "ordering": 2,
            "parent_id": res_a.resource_id,
        },
        sqla_session=db_session,
    )
    res_ac = create_entry(
        {
            "resource_id": 7,
            "resource_name": "ac",
            "ordering": 3,
            "parent_id": res_a.resource_id,
        },
        sqla_session=db_session,
    )
    res_aca = create_entry(
        {
            "resource_id": 9,
            "resource_name": "aca",
            "ordering": 1,
            "parent_id": res_ac.resource_id,
        },
        sqla_session=db_session,
    )
    res_acaa = create_entry(
        {
            "resource_id": 12,
            "resource_name": "aca",
            "ordering": 1,
            "parent_id": res_aca.resource_id,
        },
        sqla_session=db_session,
    )
    res_ad = create_entry(
        {
            "resource_id": 8,
            "resource_name": "ad",
            "ordering": 4,
            "parent_id": res_a.resource_id,
        },
        sqla_session=db_session,
    )
    res_b = create_entry(
        {
            "resource_id": 2,
            "resource_name": "b",
            "ordering": 2,
            "parent_id": root.resource_id,
        },
        sqla_session=db_session,
    )
    res_ba = create_entry(
        {
            "resource_id": 4,
            "resource_name": "ba",
            "ordering": 1,
            "parent_id": res_b.resource_id,
        },
        sqla_session=db_session,
    )
    res_c = create_entry(
        {
            "resource_id": 3,
            "resource_name": "c",
            "ordering": 3,
            "parent_id": root.resource_id,
        },
        sqla_session=db_session,
    )
    res_d = create_entry(
        {
            "resource_id": 10,
            "resource_name": "d",
            "ordering": 4,
            "parent_id": root.resource_id,
        },
        sqla_session=db_session,
    )
    res_e = create_entry(
        {
            "resource_id": 11,
            "resource_name": "e",
            "ordering": 5,
            "parent_id": root.resource_id,
        },
        sqla_session=db_session,
    )
    root_b = create_entry(
        {"resource_id": -2, "resource_name": "root b", "ordering": 2},
        sqla_session=db_session,
    )
    root_c = create_entry(
        {"resource_id": -3, "resource_name": "root 3", "ordering": 3},
        sqla_session=db_session,
    )
    return [root, root_b, root_c]


@pytest.mark.usefixtures("full_app", "with_migrations", "clean_tables", "sqla_session")
class TestFunctionalAPIEntries:
    def test_wrong_token(self, full_app):
        url_path = "/api/0.1/entries"
        headers = {str("x-testscaffold-auth-token"): str("test")}
        full_app.post(url_path, {}, status=403, headers=headers)

    def test_entries_list(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            for x in range(1, 51):
                create_entry(
                    {"resource_name": "entry-x{}".format(x), "note": "x{}".format(x)},
                    sqla_session=session,
                )
                create_entry(
                    {"resource_name": "entry-y{}".format(x), "note": "y{}".format(x)},
                    sqla_session=session,
                )

        url_path = "/api/0.1/entries"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json

        assert len(items) == 50
        assert items[0]["resource_name"] == "entry-x1"
        assert items[49]["resource_name"] == "entry-y25"
        assert response.headers["x-pages"] == "2"
        assert response.headers["x-current-page"] == "1"
        assert response.headers["x-total-count"] == "100"

    def test_entry_create_no_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/entries"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        full_app.post_json(url_path, status=422, headers=headers)

    @pytest.mark.parametrize(
        "test_input, error_keys",
        [
            ({}, ["resource_name"]),
            ({"parent_id": "v"}, ["resource_name", "parent_id"]),
            ({"ordering": 5, "resource_name": "x"}, ["ordering"]),
            ({"parent_id": 5}, ["resource_name", "parent_id"]),
        ],
    )
    def test_entry_create_bad_json(
        self, full_app, sqla_session, test_input, error_keys
    ):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/entries"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        response = full_app.post_json(url_path, test_input, status=422, headers=headers)
        assert sorted(error_keys) == sorted(response.json.keys())

    def test_entry_create(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/entries"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {
            "id": -9999,
            "resource_name": "some-new-entry",
            "note": "text",
            "ordering": 1,
        }
        response = full_app.post_json(url_path, entry_dict, status=200, headers=headers)
        assert response.json["owner_user_id"] == admin.id
        assert response.json["resource_id"] > 0
        assert response.json["ordering"] == 1
        assert entry_dict["resource_name"] == response.json["resource_name"]
        assert entry_dict["note"] == response.json["note"]

    def test_entry_patch(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            entry = create_entry(
                {"resource_name": "entry-x", "note": "x"}, sqla_session=session
            )

        url_path = "/api/0.1/entries/{}".format(entry.resource_id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"resource_id": -9, "resource_name": "CHANGED", "note": "CHANGED"}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        assert response.json["resource_id"] == entry.resource_id
        assert entry_dict["resource_name"] == response.json["resource_name"]
        assert entry_dict["note"] == response.json["note"]

    def test_entry_delete(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            entry = create_entry(
                {"resource_name": "entry-x", "note": "x"}, sqla_session=session
            )
        url_path = "/api/0.1/entries/{}".format(entry.resource_id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)
        result = tree_service.from_parent_deeper(None, db_session=sqla_session)
        assert len(result.all()) == 0

    def test_entry_delete_branch(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(1)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)
        result = tree_service.from_parent_deeper(None, db_session=sqla_session)
        row_ids = [r.Resource.resource_id for r in result]
        ordering = [r.Resource.ordering for r in result]
        assert row_ids == [-1, 2, 4, 3, 10, 11, -2, -3]
        assert ordering == [1, 1, 1, 2, 3, 4, 2, 3]

    def test_root_nesting(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        root = create_default_tree(sqla_session)[0]

        result = tree_service.from_resource_deeper(
            root.resource_id, db_session=sqla_session
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"][-1]
        pprint.pprint(tree_struct)
        assert tree_struct["node"].resource_id == -1
        l1_nodes = [n for n in tree_struct["children"].values()]
        a_node = tree_struct["children"][1]
        b_node = tree_struct["children"][2]
        ac_node = a_node["children"][7]
        l_a_nodes = [n for n in a_node["children"].values()]
        l_b_nodes = [n for n in b_node["children"].values()]
        l_ac_nodes = [n for n in ac_node["children"].values()]
        assert [n["node"].resource_id for n in l1_nodes] == [1, 2, 3, 10, 11]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert [n["node"].resource_id for n in l_b_nodes] == [4]
        assert [n["node"].resource_id for n in l_ac_nodes] == [9]

    def test_root_entry_no_parent_no_order(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = "/api/0.1/entries"

        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"id": -9999, "resource_name": "some-new-entry", "note": "text"}
        response = full_app.post_json(url_path, entry_dict, status=200, headers=headers)
        from testscaffold.services.resource_tree_service import tree_service

        result = tree_service.from_parent_deeper(
            None, db_session=sqla_session, limit_depth=1
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["resource_id"] > 0
        assert response.json["ordering"] == 4
        new_id = response.json["resource_id"]
        assert [i for i in tree_struct.keys()] == [-1, -2, -3, new_id]

    def test_root_entry_no_parent_middle(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = "/api/0.1/entries"

        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {
            "id": -9999,
            "resource_name": "some-new-entry",
            "note": "text",
            "ordering": 2,
        }
        response = full_app.post_json(url_path, entry_dict, status=200, headers=headers)
        from testscaffold.services.resource_tree_service import tree_service

        result = tree_service.from_parent_deeper(
            None, db_session=sqla_session, limit_depth=1
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)

        assert response.json["resource_id"] > 0
        assert response.json["ordering"] == 2
        new_id = response.json["resource_id"]
        assert [i for i in tree_struct.keys()] == [-1, new_id, -2, -3]

    def test_root_entry_no_parent_last(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = "/api/0.1/entries"

        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {
            "id": -9999,
            "resource_name": "some-new-entry",
            "note": "text",
            "ordering": 4,
        }
        response = full_app.post_json(url_path, entry_dict, status=200, headers=headers)
        result = tree_service.from_parent_deeper(
            None, db_session=sqla_session, limit_depth=1
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        assert response.json["resource_id"] > 0
        assert response.json["ordering"] == 4
        new_id = response.json["resource_id"]
        assert [i for i in tree_struct.keys()] == [-1, -2, -3, new_id]

    @pytest.mark.parametrize("ordering, expected", [(5, "4"), (0, "1"), (-1, "1")])
    def test_root_entry_no_parent_wrong_order(
        self, full_app, sqla_session, ordering, expected
    ):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = "/api/0.1/entries"

        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {
            "id": -9999,
            "resource_name": "some-new-entry",
            "note": "text",
            "ordering": ordering,
        }
        response = full_app.post_json(url_path, entry_dict, status=422, headers=headers)
        print(response.text)
        assert expected in response.json["ordering"][0]

    def test_entry_create_parent_no_order(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)
        url_path = "/api/0.1/entries"

        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {
            "id": -9999,
            "resource_name": "some-new-entry",
            "note": "text",
            "parent_id": 1,
        }
        response = full_app.post_json(url_path, entry_dict, status=200, headers=headers)
        result = tree_service.from_parent_deeper(
            1, db_session=sqla_session, limit_depth=1
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["resource_id"] > 0
        assert response.json["ordering"] == 5
        new_id = response.json["resource_id"]
        assert [i for i in tree_struct.keys()] == [5, 6, 7, 8, new_id]

    def test_entry_patch_same_parent(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(1)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"parent_id": -1}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        result = tree_service.from_parent_deeper(None, db_session=sqla_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["ordering"] == 1

    def test_entry_patch_order_same_branch(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(-2)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"ordering": 3}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        result = tree_service.from_parent_deeper(None, db_session=sqla_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["ordering"] == 3
        assert [i for i in tree_struct.keys()] == [-1, -3, -2]
        assert [i["node"].ordering for i in tree_struct.values()] == [1, 2, 3]

    @pytest.mark.parametrize(
        "node_id, position, ordered_elems",
        [
            (6, 3, [5, 7, 6, 8]),
            (6, 1, [6, 5, 7, 8]),
            (6, 2, [5, 6, 7, 8]),
            (6, 4, [5, 7, 8, 6]),
        ],
    )
    def test_entry_patch_order_same_branch_nested(
        self, full_app, sqla_session, node_id, position, ordered_elems
    ):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(node_id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"ordering": position}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        result = tree_service.from_parent_deeper(1, db_session=sqla_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["ordering"] == position
        assert [i for i in tree_struct.keys()] == ordered_elems
        assert [i["node"].ordering for i in tree_struct.values()] == [1, 2, 3, 4]

    @pytest.mark.parametrize(
        "node_id, position, ordered_elems",
        [
            (12, 3, [5, 6, 12, 7, 8]),
            (12, 1, [12, 5, 6, 7, 8]),
            (12, 2, [5, 12, 6, 7, 8]),
            (12, 5, [5, 6, 7, 8, 12]),
        ],
    )
    def test_entry_patch_order_upper_branch_nested(
        self, full_app, sqla_session, node_id, position, ordered_elems
    ):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(node_id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"ordering": position, "parent_id": 1}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        result = tree_service.from_parent_deeper(1, db_session=sqla_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["ordering"] == position
        assert [i for i in tree_struct.keys()] == ordered_elems
        assert [i["node"].ordering for i in tree_struct.values()] == [1, 2, 3, 4, 5]

    def test_entry_patch_order_upper_branch_no_order(self, full_app, sqla_session):
        from testscaffold.services.resource_tree_service import tree_service

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_default_tree(db_session=sqla_session)

        url_path = "/api/0.1/entries/{}".format(12)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        entry_dict = {"parent_id": 1}
        response = full_app.patch_json(
            url_path, entry_dict, status=200, headers=headers
        )
        result = tree_service.from_parent_deeper(1, db_session=sqla_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        assert response.json["ordering"] == 5
        assert [i for i in tree_struct.keys()] == [5, 6, 7, 8, 12]
        assert [i["node"].ordering for i in tree_struct.values()] == [1, 2, 3, 4, 5]
