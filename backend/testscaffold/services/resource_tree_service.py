from ziggurat_foundations.models.services.resource_tree import ResourceTreeService
from ziggurat_foundations.models.services.resource_tree_postgres import (
    ResourceTreeServicePostgreSQL,
)

tree_service = ResourceTreeService(ResourceTreeServicePostgreSQL)
