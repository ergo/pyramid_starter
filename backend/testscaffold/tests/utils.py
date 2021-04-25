from contextlib import contextmanager

from testscaffold.models import (
    Group,
    GroupPermission,
    User,
    AuthToken,
    Entry,
    UserPermission,
)


def create_admin(session):
    admin = create_user(
        {"user_name": "test", "email": "test@test.local"}, permissions=["root_administration"], sqla_session=session,
    )
    token = admin.auth_tokens[0].token
    return admin, token


def create_group(group_dict, permissions=None, sqla_session=None):
    group = Group(**group_dict)
    if permissions:
        for perm_name in permissions:
            permission_instance = GroupPermission(perm_name=perm_name)
            group.permissions.append(permission_instance)
    group.persist(flush=True, db_session=sqla_session)
    return group


def create_user(user_dict, permissions=None, sqla_session=None):
    user = User(**user_dict)
    user.auth_tokens.append(AuthToken())
    if permissions:
        for perm_name in permissions:
            permission_instance = UserPermission(perm_name=perm_name)
            user.user_permissions.append(permission_instance)
    user.persist(flush=True, db_session=sqla_session)
    return user


def create_entry(entry_dict, sqla_session=None):
    entry = Entry(**entry_dict)
    entry.persist(flush=True, db_session=sqla_session)
    return entry


@contextmanager
def session_context(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.commit()
    finally:
        session.rollback()


@contextmanager
def tmp_session_context(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.rollback()
    finally:
        session.rollback()
