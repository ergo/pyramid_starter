# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.group_resource_permission import \
    GroupResourcePermissionMixin

from testscaffold.models.meta import Base


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass
