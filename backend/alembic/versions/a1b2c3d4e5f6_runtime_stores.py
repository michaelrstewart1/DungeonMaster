"""runtime stores table

Revision ID: a1b2c3d4e5f6
Revises: 8dfce592ee33
Create Date: 2026-07-29

Persists runtime state (room codes, session players, trades, auth tokens,
vision analyses) so live sessions survive backend restarts.
"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "8dfce592ee33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_stores",
        sa.Column("name", sa.String(length=64), primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runtime_stores")
