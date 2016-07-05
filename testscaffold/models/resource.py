# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.resource import ResourceMixin
from testscaffold.models.meta import Base


class Resource(ResourceMixin, Base):
    pass
