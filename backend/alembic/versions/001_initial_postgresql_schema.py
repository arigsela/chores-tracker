"""Initial PostgreSQL schema - consolidated from MySQL migrations

Revision ID: 001_pg_initial
Revises:
Create Date: 2025-12-03

This migration consolidates all MySQL migrations into a single PostgreSQL-native schema.
It creates all tables with proper PostgreSQL types and triggers for updated_at columns.

Tables created:
- families: Family groupings for users
- users: User accounts (parents and children)
- chores: Chore definitions with assignment modes
- chore_assignments: Many-to-many relationship between chores and users
- reward_adjustments: Manual balance adjustments by parents
- activities: Activity logging for audit trail

PostgreSQL-specific features:
- JSONB for activity_data (better performance than JSON)
- Triggers for automatic updated_at timestamp updates
- Explicit foreign key constraint names for easier management
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_pg_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for PostgreSQL."""

    # =========================================================================
    # STEP 1: Create the updated_at trigger function
    # =========================================================================
    # This function will be used by all tables that need automatic updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================================
    # STEP 2: Create FAMILIES table
    # =========================================================================
    op.create_table('families',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('invite_code', sa.String(length=8), nullable=False),
        sa.Column('invite_code_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_families')
    )
    op.create_index('ix_families_id', 'families', ['id'], unique=False)
    op.create_index('ix_families_invite_code', 'families', ['invite_code'], unique=True)

    # Trigger for families.updated_at
    op.execute("""
        CREATE TRIGGER trg_families_updated_at
        BEFORE UPDATE ON families
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # =========================================================================
    # STEP 3: Create USERS table
    # =========================================================================
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_parent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('family_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], name='fk_users_parent_id'),
        sa.ForeignKeyConstraint(['family_id'], ['families.id'], name='fk_users_family_id'),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_family_id', 'users', ['family_id'], unique=False)
    op.create_index('idx_users_parent_id', 'users', ['parent_id'], unique=False)

    # Trigger for users.updated_at
    op.execute("""
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # =========================================================================
    # STEP 4: Create CHORES table
    # =========================================================================
    op.create_table('chores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        # Reward settings
        sa.Column('reward', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('min_reward', sa.Float(), nullable=True),
        sa.Column('max_reward', sa.Float(), nullable=True),
        sa.Column('is_range_reward', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        # Recurrence settings
        sa.Column('cooldown_days', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('frequency', sa.String(length=50), nullable=True),  # Deprecated, kept for compatibility
        # Assignment mode: 'single', 'multi_independent', 'unassigned'
        sa.Column('assignment_mode', sa.String(length=20), nullable=False, server_default=sa.text("'single'")),
        # Status
        sa.Column('is_disabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        # Legacy fields (kept for backward compatibility with older data)
        sa.Column('approval_reward', sa.Float(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        # Foreign keys
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], name='fk_chores_creator_id'),
        sa.PrimaryKeyConstraint('id', name='pk_chores')
    )
    op.create_index('ix_chores_id', 'chores', ['id'], unique=False)
    op.create_index('ix_chores_title', 'chores', ['title'], unique=False)
    op.create_index('idx_chores_assignment_mode', 'chores', ['assignment_mode'], unique=False)
    op.create_index('idx_chores_creator_id', 'chores', ['creator_id'], unique=False)
    op.create_index('idx_chores_created_at', 'chores', ['created_at'], unique=False)
    op.create_index('idx_chores_status', 'chores', ['is_disabled'], unique=False)

    # Trigger for chores.updated_at
    op.execute("""
        CREATE TRIGGER trg_chores_updated_at
        BEFORE UPDATE ON chores
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # =========================================================================
    # STEP 5: Create CHORE_ASSIGNMENTS table
    # =========================================================================
    op.create_table('chore_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chore_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=False),
        # Completion tracking
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        # Reward tracking
        sa.Column('approval_reward', sa.Float(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        # Foreign keys with CASCADE delete
        sa.ForeignKeyConstraint(['chore_id'], ['chores.id'], name='fk_assignments_chore_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], name='fk_assignments_assignee_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_chore_assignments'),
        # Unique constraint: one assignment per user per chore
        sa.UniqueConstraint('chore_id', 'assignee_id', name='uq_chore_assignee')
    )
    op.create_index('idx_assignments_chore_id', 'chore_assignments', ['chore_id'], unique=False)
    op.create_index('idx_assignments_assignee_id', 'chore_assignments', ['assignee_id'], unique=False)
    op.create_index('idx_assignments_is_completed', 'chore_assignments', ['is_completed'], unique=False)
    op.create_index('idx_assignments_is_approved', 'chore_assignments', ['is_approved'], unique=False)

    # Trigger for chore_assignments.updated_at
    op.execute("""
        CREATE TRIGGER trg_chore_assignments_updated_at
        BEFORE UPDATE ON chore_assignments
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # =========================================================================
    # STEP 6: Create REWARD_ADJUSTMENTS table
    # =========================================================================
    op.create_table('reward_adjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['users.id'], name='fk_adjustments_child_id'),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], name='fk_adjustments_parent_id'),
        sa.PrimaryKeyConstraint('id', name='pk_reward_adjustments')
    )
    op.create_index('ix_reward_adjustments_id', 'reward_adjustments', ['id'], unique=False)
    op.create_index('idx_adjustments_child_id', 'reward_adjustments', ['child_id'], unique=False)
    op.create_index('idx_adjustments_parent_id', 'reward_adjustments', ['parent_id'], unique=False)

    # =========================================================================
    # STEP 7: Create ACTIVITIES table
    # =========================================================================
    # Using JSONB instead of JSON for better PostgreSQL performance
    op.create_table('activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        # JSONB for better query performance in PostgreSQL
        sa.Column('activity_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_activities_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], name='fk_activities_target_user_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_activities')
    )
    op.create_index('ix_activities_id', 'activities', ['id'], unique=False)
    op.create_index('ix_activities_user_id', 'activities', ['user_id'], unique=False)
    op.create_index('ix_activities_activity_type', 'activities', ['activity_type'], unique=False)
    op.create_index('ix_activities_created_at', 'activities', ['created_at'], unique=False)
    # GIN index for JSONB queries (PostgreSQL-specific optimization)
    op.execute("""
        CREATE INDEX idx_activities_data_gin ON activities USING GIN (activity_data);
    """)


def downgrade() -> None:
    """Drop all tables and triggers."""

    # =========================================================================
    # Drop tables in reverse order (respecting foreign key dependencies)
    # =========================================================================

    # Drop activities table and its GIN index
    op.execute("DROP INDEX IF EXISTS idx_activities_data_gin;")
    op.drop_index('ix_activities_created_at', table_name='activities')
    op.drop_index('ix_activities_activity_type', table_name='activities')
    op.drop_index('ix_activities_user_id', table_name='activities')
    op.drop_index('ix_activities_id', table_name='activities')
    op.drop_table('activities')

    # Drop reward_adjustments table
    op.drop_index('idx_adjustments_parent_id', table_name='reward_adjustments')
    op.drop_index('idx_adjustments_child_id', table_name='reward_adjustments')
    op.drop_index('ix_reward_adjustments_id', table_name='reward_adjustments')
    op.drop_table('reward_adjustments')

    # Drop chore_assignments table (trigger dropped automatically with table)
    op.drop_index('idx_assignments_is_approved', table_name='chore_assignments')
    op.drop_index('idx_assignments_is_completed', table_name='chore_assignments')
    op.drop_index('idx_assignments_assignee_id', table_name='chore_assignments')
    op.drop_index('idx_assignments_chore_id', table_name='chore_assignments')
    op.drop_table('chore_assignments')

    # Drop chores table (trigger dropped automatically with table)
    op.drop_index('idx_chores_status', table_name='chores')
    op.drop_index('idx_chores_created_at', table_name='chores')
    op.drop_index('idx_chores_creator_id', table_name='chores')
    op.drop_index('idx_chores_assignment_mode', table_name='chores')
    op.drop_index('ix_chores_title', table_name='chores')
    op.drop_index('ix_chores_id', table_name='chores')
    op.drop_table('chores')

    # Drop users table (trigger dropped automatically with table)
    op.drop_index('idx_users_parent_id', table_name='users')
    op.drop_index('ix_users_family_id', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')

    # Drop families table (trigger dropped automatically with table)
    op.drop_index('ix_families_invite_code', table_name='families')
    op.drop_index('ix_families_id', table_name='families')
    op.drop_table('families')

    # =========================================================================
    # Drop the trigger function (must be done after all tables are dropped)
    # =========================================================================
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
