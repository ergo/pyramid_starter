# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import sqlalchemy as sa
from testscaffold.models.user import User
from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services.user import UserService as UService
from paginate_sqlalchemy import SqlalchemyOrmPage

log = logging.getLogger(__name__)


class UserService(UService):
    @classmethod
    def latest_registered_user(cls, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(User).order_by(sa.desc(User.id)).first()

    @classmethod
    def latest_logged_user(cls, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(User).order_by(
            sa.desc(User.last_login_date)).first()

    @classmethod
    def total_count(cls, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(User).count()

    @classmethod
    def get_paginator(cls, page=1, item_count=None, items_per_page=50,
                      db_session=None,
                      filter_params=None, **kwargs):
        """ returns paginator over users belonging to the group"""
        if filter_params is None:
            filter_params = {}
        db_session = get_db_session(db_session)
        query = db_session.query(User)
        user_name_like = filter_params.get('user_name_like')
        if user_name_like:
            query = query.filter(User.user_name.like(user_name_like + '%'))
        query = query.order_by(User.id)
        return SqlalchemyOrmPage(query, page=page, item_count=item_count,
                                 items_per_page=items_per_page,
                                 **kwargs)

    @classmethod
    def permission_info(cls, user):
        return {
            'system_permissions': [p.perm_name for p in user.permissions],
            'resource_permissions': user.resources_with_perms(['owner'])
        }