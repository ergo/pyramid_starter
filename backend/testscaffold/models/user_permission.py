from ziggurat_foundations.models.user_permission import UserPermissionMixin

from testscaffold.models.meta import Base


class UserPermission(UserPermissionMixin, Base):
    pass
