import pytest
from six.moves.urllib import parse

from testscaffold.tests.utils import create_user, session_context, create_admin


@pytest.mark.usefixtures("full_app", "with_migrations", "clean_tables", "sqla_session")
class TestFunctionalAPIUsers:
    def test_wrong_token(self, full_app):
        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str("test")}
        full_app.post(url_path, {}, status=403, headers=headers)

    def test_users_list(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_user(
                {"user_name": "test2", "email": "test@test.local2"}, sqla_session=session,
            )

        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json
        assert len(items) == 2

    def test_users_filtering(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            create_user(
                {"user_name": "test2", "email": "test@test.local2"}, sqla_session=session,
            )
            create_user({"user_name": "foo", "email": "test2@test.local2"}, sqla_session=session)
            create_user(
                {"user_name": "barbaz", "email": "test3@test.local2"}, sqla_session=session,
            )

        url_path = "/api/0.1/users?user_name_like=bar"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        response = full_app.get(url_path, status=200, headers=headers)
        items = response.json
        assert items[0]["user_name"] == "barbaz"

    def test_user_create_no_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        full_app.post_json(url_path, status=422, headers=headers)

    def test_user_create_bad_json(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        user_dict = {"xxx": "yyy"}
        response = full_app.post_json(url_path, user_dict, status=422, headers=headers)
        required = ["user_name", "email", "password"]
        assert sorted(required) == sorted(response.json.keys())

    def test_user_create(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        user_dict = {
            "id": -9999,
            "user_name": "some-new_user",
            "password": "new_password",
            "email": "email@foo.bar",
        }
        response = full_app.post_json(url_path, user_dict, status=200, headers=headers)
        assert response.json["id"] > 0
        assert user_dict["user_name"] == response.json["user_name"]
        assert user_dict["email"] == response.json["email"]
        assert "last_login_date" in response.json
        assert "registered_date" in response.json
        assert response.json["status"] == 1

    def test_user_duplicate(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)

        url_path = "/api/0.1/users"
        headers = {str("x-testscaffold-auth-token"): str(token)}
        user_dict = {
            "id": -9999,
            "user_name": "test",
            "password": "new_password",
            "email": "email@foo.bar",
        }
        response = full_app.post_json(url_path, user_dict, status=422, headers=headers)
        assert response.json["user_name"]

    def test_user_patch(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({"user_name": "testX", "email": "testX@test.local"}, sqla_session=session,)

        url_path = "/api/0.1/users/{}".format(user.id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        user_dict = {
            "id": -9,
            "user_name": "some-new_userCHANGED",
            "email": "email@fooCHANGED.bar",
        }
        response = full_app.patch_json(url_path, user_dict, status=200, headers=headers)
        assert response.json["id"] == user.id
        assert user_dict["user_name"] == response.json["user_name"]
        assert user_dict["email"] == response.json["email"]

    def test_user_delete(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({"user_name": "testX", "email": "testX@test.local"}, sqla_session=session,)
        url_path = "/api/0.1/users/{}".format(user.id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        full_app.delete_json(url_path, status=200, headers=headers)


@pytest.mark.usefixtures("full_app", "with_migrations", "clean_tables", "sqla_session")
class TestFunctionalAPIUsersPermissions:
    def test_permission_add(self, full_app, sqla_session):
        from ziggurat_foundations.models.services.user import UserService

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({"user_name": "testX", "email": "testX@test.local"}, sqla_session=session,)

        url_path = "/api/0.1/users/{}/permissions".format(user.id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        permission = {"perm_name": "root_administration"}
        permissions = UserService.permissions(user)
        assert not list(permissions)
        full_app.post_json(url_path, permission, status=200, headers=headers)
        sqla_session.expire_all()
        permissions = UserService.permissions(user)
        assert permissions[0].perm_name == "root_administration"

    def test_permission_delete_not_found(self, full_app, sqla_session):
        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user({"user_name": "testX", "email": "testX@test.local"}, sqla_session=session,)

        url_path = "/api/0.1/users/{}/permissions".format(user.id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        permission = {"perm_name": "c"}
        full_app.delete(url_path, permission, status=404, headers=headers)

    def test_permission_delete(self, full_app, sqla_session):
        from ziggurat_foundations.models.services.user import UserService

        with session_context(sqla_session) as session:
            admin, token = create_admin(session)
            user = create_user(
                {"user_name": "testX", "email": "testX@test.local"},
                permissions=["root_administration", "admin_panel"],
                sqla_session=session,
            )

        url_path = "/api/0.1/users/{}/permissions".format(user.id)
        headers = {str("x-testscaffold-auth-token"): str(token)}
        permission = {"perm_name": "root_administration"}
        qs = parse.urlencode(permission)
        full_app.delete("{}?{}".format(url_path, qs), status=200, headers=headers)
        sqla_session.expire_all()
        permissions = UserService.permissions(user)
        assert permissions[0].perm_name == "admin_panel"
