"""initial schema

Revision ID: 8dfce592ee33
Revises: 
Create Date: 2026-04-10 10:48:03.585221

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8dfce592ee33'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('campaigns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('character_ids', sa.JSON(), nullable=False),
        sa.Column('world_state', sa.JSON(), nullable=False),
        sa.Column('dm_settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
        sa.Column('session_summary', sa.Text(), nullable=True),
        sa.Column('story_bible', sa.Text(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_table('characters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('race', sa.String(length=50), nullable=False),
        sa.Column('class_name', sa.String(length=50), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('strength', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('dexterity', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('constitution', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('intelligence', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('wisdom', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('charisma', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('hp', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('max_hp', sa.Integer(), nullable=True),
        sa.Column('ac', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('speed', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('experience_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('subrace', sa.String(length=100), nullable=True),
        sa.Column('subclass', sa.String(length=100), nullable=True),
        sa.Column('background', sa.String(length=100), nullable=True),
        sa.Column('alignment', sa.String(length=50), nullable=True),
        sa.Column('hit_dice', sa.String(length=20), nullable=True),
        sa.Column('portrait_url', sa.Text(), nullable=True),
        sa.Column('personality_traits', sa.Text(), nullable=True),
        sa.Column('ideals', sa.Text(), nullable=True),
        sa.Column('bonds', sa.Text(), nullable=True),
        sa.Column('flaws', sa.Text(), nullable=True),
        sa.Column('backstory', sa.Text(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=False),
        sa.Column('saving_throws', sa.JSON(), nullable=False),
        sa.Column('languages', sa.JSON(), nullable=False),
        sa.Column('tool_proficiencies', sa.JSON(), nullable=False),
        sa.Column('armor_proficiencies', sa.JSON(), nullable=False),
        sa.Column('weapon_proficiencies', sa.JSON(), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('spells_known', sa.JSON(), nullable=False),
        sa.Column('cantrips_known', sa.JSON(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('inventory', sa.JSON(), nullable=False),
        sa.Column('equipment', sa.JSON(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('current_phase', sa.String(length=50), nullable=False, server_default='exploration'),
        sa.Column('current_scene', sa.Text(), nullable=False, server_default=''),
        sa.Column('turn_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('narrative_history', sa.JSON(), nullable=False),
        sa.Column('combat_state', sa.JSON(), nullable=True),
        sa.Column('active_effects', sa.JSON(), nullable=False),
        sa.Column('environment', sa.JSON(), nullable=False),
        sa.Column('npcs', sa.JSON(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('maps',
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('terrain_grid', sa.JSON(), nullable=False),
        sa.Column('token_positions', sa.JSON(), nullable=False),
        sa.Column('fog_of_war', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('session_id')
    )


def downgrade() -> None:
    op.drop_table('maps')
    op.drop_table('game_sessions')
    op.drop_table('characters')
    op.drop_table('users')
    op.drop_table('campaigns')
