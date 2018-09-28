# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ziggurat_foundations.models.services.resource_tree import ResourceTreeService
from ziggurat_foundations.models.services.resource_tree_postgres import (
    ResourceTreeServicePostgreSQL,
)

tree_service = ResourceTreeService(ResourceTreeServicePostgreSQL)
