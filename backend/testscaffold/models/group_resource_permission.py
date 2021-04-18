from ziggurat_foundations.models.group_resource_permission import (
    GroupResourcePermissionMixin,
)

from testscaffold.models.meta import Base


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass
