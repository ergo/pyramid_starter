# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from pyramid.security import Allow, ALL_PERMISSIONS
from ziggurat_foundations.models.resource import ResourceMixin

from testscaffold.models.meta import Base


class Resource(ResourceMixin, Base):
    @property
    def __acl__(self):
        acls = []

        if self.owner_user_id:
            acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS)])

        if self.owner_group_id:
            acls.extend([(Allow, "group:%s" % self.owner_group_id, ALL_PERMISSIONS)])
        return acls
