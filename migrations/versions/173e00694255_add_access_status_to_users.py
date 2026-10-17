
"""add access status to users

Revision ID: 173e00694255
Revises: 03806f7380c8
Create Date: 2026-10-14 02:45:41.404876
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "173e00694255"
down_revision: Union[str, Sequence[str], None] = "03806f7380c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # The previous migration attempt may have added the column
    # before failing. Check before adding it again.
    inspector = sa.inspect(op.get_bind())
    columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "access_status" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "access_status",
                sa.String(length=50),
                nullable=False,
                server_default="ACTIVE",
            ),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "access_status" in columns:
        op.drop_column("users", "access_status")
