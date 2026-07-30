"""campaign memory table

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-29

Structured long-term DM memory per campaign: canonical event log, quest
log, persistent NPC registry, and known locations. This is what keeps the
AI DM's dialog consistent across turns and sessions.
"""
from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_memory",
        sa.Column("campaign_id", sa.String(length=36), primary_key=True),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("quests", sa.JSON(), nullable=False),
        sa.Column("npcs", sa.JSON(), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("campaign_memory")
