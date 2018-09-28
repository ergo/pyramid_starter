# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

from paginate_sqlalchemy import SqlalchemyOrmPage
from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services.group import GroupService as GService

from testscaffold.models.group import Group

log = logging.getLogger(__name__)


class GroupService(GService):
    @classmethod
    def get(cls, group_id, db_session=None):
        """ get group by primary key from session """
        if not group_id:
            return None
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        return query.get(group_id)

    @classmethod
    def by_id(cls, group_id, db_session=None):
        """ fetch user by user id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        query = query.filter(cls.model.id == group_id)
        return query.first()

    @classmethod
    def get_paginator(
        cls, page=1, item_count=None, items_per_page=50, db_session=None, **kwargs
    ):
        """ returns paginator over users belonging to the group"""
        db_session = get_db_session(db_session)
        query = db_session.query(Group)
        query = query.order_by(Group.group_name)
        return SqlalchemyOrmPage(
            query,
            page=page,
            item_count=item_count,
            items_per_page=items_per_page,
            **kwargs
        )

    @classmethod
    def get_user_paginator(
        cls,
        group,
        page=1,
        item_count=None,
        items_per_page=50,
        db_session=None,
        **kwargs
    ):
        """ returns paginator over users belonging to the group"""
        query = group.users_dynamic
        return SqlalchemyOrmPage(
            query,
            page=page,
            item_count=item_count,
            items_per_page=items_per_page,
            **kwargs
        )
