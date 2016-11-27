# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sqlalchemy as sa
from ziggurat_foundations.models.base import BaseModel

from testscaffold.models.meta import Base
from testscaffold.services.user import UserService


class AuthToken(BaseModel, Base):
    """
    Auth tokens that can be used to authenticate as specific users
    """
    __tablename__ = 'auth_tokens'

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    token = sa.Column(sa.Unicode(40), nullable=False,
                      default=lambda x: UserService.generate_random_string(40))
    owner_id = sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='CASCADE'))
