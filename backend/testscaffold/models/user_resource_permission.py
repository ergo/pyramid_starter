from ziggurat_foundations.models.user_resource_permission import (
    UserResourcePermissionMixin,
)

from testscaffold.models.meta import Base


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass
