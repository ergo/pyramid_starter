from ziggurat_foundations.models.group import GroupMixin

from testscaffold.models.meta import Base


class Group(GroupMixin, Base):
    __possible_permissions__ = (
        "root_administration",
        "admin_panel",
        "admin_users",
        "admin_groups",
        "admin_entries",
    )
