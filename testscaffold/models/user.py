# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sqlalchemy as sa
from ziggurat_foundations.models.user import UserMixin
from testscaffold.models.meta import Base


class User(UserMixin, Base):
    __possible_permissions__ = ['root_administration', 'dummy_permission']

    # registration_ip = sa.Column(sa.Unicode())

    auth_tokens = sa.orm.relationship('AuthToken',
                                      cascade="all,delete-orphan",
                                      passive_deletes=True,
                                      passive_updates=True,
                                      backref='owner',
                                      order_by='AuthToken.id')

    def get_dict(self, exclude_keys=None, include_keys=None,
                 permission_info=False):
        if exclude_keys is None:
            exclude_keys = ['user_password', 'security_code',
                            'security_code_date']

        user_dict = super(User, self).get_dict(exclude_keys=exclude_keys,
                                               include_keys=include_keys)
        return user_dict

    def permission_info(self):
        return {
            'system_permissions': [p.perm_name for p in self.permissions],
            'resource_permissions': self.resources_with_perms(['owner'])
        }

    def __json__(self, request):
        return self.get_dict()
