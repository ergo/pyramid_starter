import sqlalchemy as sa

from testscaffold.models.resource import Resource


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
        sa.Integer(),
        sa.ForeignKey("resources.resource_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )

    note = sa.Column(sa.UnicodeText())
