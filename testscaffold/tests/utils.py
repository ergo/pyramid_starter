# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from contextlib import contextmanager
from testscaffold.models import User, AuthToken, UserPermission


def create_user(user_dict, permissions=None, sqla_session=None):
    user = User(**user_dict)
    user.auth_tokens.append(AuthToken())
    if permissions:
        for perm_name in permissions:
            permission_instance = UserPermission(perm_name=perm_name)
            user.user_permissions.append(permission_instance)
    user.persist(flush=True, db_session=sqla_session)
    return user


@contextmanager
def session_context(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        print('CLOSING')
        session.close()


@contextmanager
def tmp_session_context(session):
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.rollback()
    except:
        session.rollback()
        raise
    finally:
        print('CLOSING')
        session.close()
