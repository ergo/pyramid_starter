from ziggurat_foundations.models.group_permission import GroupPermissionMixin

from testscaffold.models.meta import Base


class GroupPermission(GroupPermissionMixin, Base):
    pass
