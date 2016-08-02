# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.group import GroupMixin
from testscaffold.models.meta import Base


class Group(GroupMixin, Base):
    __possible_permissions__ = ('root_administration', 'dummy_permission')
