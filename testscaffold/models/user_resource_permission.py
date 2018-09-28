# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.user_resource_permission import (
    UserResourcePermissionMixin,
)

from testscaffold.models.meta import Base


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass
