"""add_multi_assignment_support

Revision ID: 0582f39dfdd4
Revises: a988bdaeacef
Create Date: 2025-10-14 00:43:09.120239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0582f39dfdd4'
down_revision: Union[str, None] = 'a988bdaeacef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to support multi-assignment chores."""
    # Create chore_assignments table
    op.create_table(
        'chore_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chore_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('approval_reward', sa.Float(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chore_id'], ['chores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('chore_id', 'assignee_id', name='unique_chore_assignee')
    )

    # Add indexes for performance
    op.create_index('idx_assignments_chore', 'chore_assignments', ['chore_id'])
    op.create_index('idx_assignments_assignee', 'chore_assignments', ['assignee_id'])
    op.create_index('idx_assignments_completed', 'chore_assignments', ['is_completed'])

    # Add assignment_mode column to chores table
    op.add_column('chores', sa.Column('assignment_mode', sa.String(length=20), nullable=False, server_default='single'))
    op.create_index('idx_chores_mode', 'chores', ['assignment_mode'])

    # Remove old single-assignment fields from chores table
    # Note: In production, you might want to migrate data first before dropping columns
    # Since we're starting from scratch per requirements, we can safely drop these

    # Drop foreign key constraint first (MySQL requirement)
    op.drop_constraint('chores_ibfk_1', 'chores', type_='foreignkey')

    # Now drop the columns
    op.drop_column('chores', 'assignee_id')
    op.drop_column('chores', 'is_completed')
    op.drop_column('chores', 'is_approved')
    op.drop_column('chores', 'completion_date')


def downgrade() -> None:
    """Downgrade schema to remove multi-assignment support."""
    # Add back old single-assignment fields to chores table
    op.add_column('chores', sa.Column('completion_date', sa.DateTime(), nullable=True))
    op.add_column('chores', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('chores', sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('chores', sa.Column('assignee_id', sa.Integer(), nullable=True))
    op.create_foreign_key('chores_ibfk_1', 'chores', 'users', ['assignee_id'], ['id'])

    # Remove assignment_mode column and index
    op.drop_index('idx_chores_mode', 'chores')
    op.drop_column('chores', 'assignment_mode')

    # Drop indexes on chore_assignments
    op.drop_index('idx_assignments_completed', 'chore_assignments')
    op.drop_index('idx_assignments_assignee', 'chore_assignments')
    op.drop_index('idx_assignments_chore', 'chore_assignments')

    # Drop chore_assignments table
    op.drop_table('chore_assignments')
