"""initial migration

Revision ID: afe8882875e5
Revises:
Create Date: 2016-04-03 11:26:28.732074

"""
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "afe8882875e5"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "entries",
        sa.Column(
            "resource_id",
            sa.Integer(),
            sa.ForeignKey(
                "resources.resource_id", onupdate="CASCADE", ondelete="CASCADE"
            ),
            primary_key=True,
        ),
        sa.Column("note", sa.UnicodeText()),
    )

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer, nullable=False, primary_key=True),
        sa.Column("token", sa.Unicode),
        sa.Column(
            "owner_id",
            sa.Integer,
            sa.ForeignKey("users.id", onupdate="cascade", ondelete="cascade"),
        ),
    )


def downgrade():
    pass
