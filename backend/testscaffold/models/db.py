import sqlalchemy as sa

from pyramid.security import Allow, ALL_PERMISSIONS
from sqlalchemy.orm import declared_attr

from ziggurat_foundations.models.base import BaseModel
from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
from ziggurat_foundations.models.group import GroupMixin
from ziggurat_foundations.models.group_permission import GroupPermissionMixin
from ziggurat_foundations.models.group_resource_permission import GroupResourcePermissionMixin
from ziggurat_foundations.models.resource import ResourceMixin
from ziggurat_foundations.models.services.user import UserService as ZUserService
from ziggurat_foundations.models.user import UserMixin
from ziggurat_foundations.models.user_group import UserGroupMixin
from ziggurat_foundations.models.user_permission import UserPermissionMixin
from ziggurat_foundations.models.user_resource_permission import UserResourcePermissionMixin

from testscaffold.util.sqlalchemy import EncryptedUnicode
from testscaffold.models.meta import Base


class AuthToken(BaseModel, Base):
    """
    Auth tokens that can be used to authenticate as specific users
    """

    __tablename__ = "auth_tokens"

    id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    token = sa.Column(sa.Unicode(40), nullable=False, default=lambda x: ZUserService.generate_random_string(40),)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))


class ExternalIdentity(ExternalIdentityMixin, Base):
    @declared_attr
    def access_token(self):
        return sa.Column(EncryptedUnicode(255), default="")

    @declared_attr
    def alt_token(self):
        return sa.Column(EncryptedUnicode(255), default="")

    @declared_attr
    def token_secret(self):
        return sa.Column(EncryptedUnicode(255), default="")


class Group(GroupMixin, Base):
    __possible_permissions__ = (
        "root_administration",
        "admin_panel",
        "admin_users",
        "admin_groups",
        "admin_entries",
    )


class GroupPermission(GroupPermissionMixin, Base):
    pass


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class UserPermission(UserPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base):
    pass


class User(UserMixin, Base):
    __possible_permissions__ = [
        "root_administration",
        "admin_panel",
        "admin_users",
        "admin_groups",
        "admin_entries",
    ]

    # registration_ip = sa.Column(sa.Unicode())

    auth_tokens = sa.orm.relationship(
        "AuthToken",
        cascade="all,delete-orphan",
        passive_deletes=True,
        passive_updates=True,
        backref="owner",
        order_by="AuthToken.id",
    )

    def get_dict(self, exclude_keys=None, include_keys=None, permission_info=False):
        if exclude_keys is None:
            exclude_keys = ["user_password", "security_code", "security_code_date"]

        user_dict = super(User, self).get_dict(exclude_keys=exclude_keys, include_keys=include_keys)
        return user_dict


class Resource(ResourceMixin, Base):
    @property
    def __acl__(self):
        acls = []

        if self.owner_user_id:
            acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS)])

        if self.owner_group_id:
            acls.extend([(Allow, "group:%s" % self.owner_group_id, ALL_PERMISSIONS)])
        return acls


class Entry(Resource):
    """
    Resource of application type
    """

    __tablename__ = "entries"
    __mapper_args__ = {"polymorphic_identity": "entry"}

    __possible_permissions__ = ["view", "edit"]

    # handy for generic redirections based on type
    plural_type = "entries"

    resource_id = sa.Column(
        sa.Integer(), sa.ForeignKey("resources.resource_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True,
    )

    note = sa.Column(sa.UnicodeText())
