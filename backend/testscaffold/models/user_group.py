from ziggurat_foundations.models.user_group import UserGroupMixin

from testscaffold.models.meta import Base


class UserGroup(UserGroupMixin, Base):
    pass
