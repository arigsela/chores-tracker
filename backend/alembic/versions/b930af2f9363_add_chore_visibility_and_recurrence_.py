"""add chore visibility and recurrence fields

Revision ID: b930af2f9363
Revises: fd1e718695e9
Create Date: 2025-07-28 11:51:40.857740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b930af2f9363'
down_revision: Union[str, None] = 'fd1e718695e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create chore_visibility table
    op.create_table('chore_visibility',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chore_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['chore_id'], ['chores.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chore_id', 'user_id', name='unique_chore_user')
    )
    
    # Create indexes for chore_visibility
    op.create_index('idx_chore_id', 'chore_visibility', ['chore_id'], unique=False)
    op.create_index('idx_user_id_hidden', 'chore_visibility', ['user_id', 'is_hidden'], unique=False)
    
    # Add recurrence fields to chores table
    op.add_column('chores', sa.Column('recurrence_type', sa.Enum('none', 'daily', 'weekly', 'monthly', name='recurrencetype'), nullable=False, server_default='none'))
    op.add_column('chores', sa.Column('recurrence_value', sa.Integer(), nullable=True))
    op.add_column('chores', sa.Column('last_completion_time', sa.DateTime(), nullable=True))
    op.add_column('chores', sa.Column('next_available_time', sa.DateTime(), nullable=True))
    
    # Create indexes for the new chores columns
    op.create_index('idx_next_available', 'chores', ['next_available_time'], unique=False)
    op.create_index('idx_recurrence', 'chores', ['recurrence_type', 'next_available_time'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes from chores table
    op.drop_index('idx_recurrence', table_name='chores')
    op.drop_index('idx_next_available', table_name='chores')
    
    # Remove columns from chores table
    op.drop_column('chores', 'next_available_time')
    op.drop_column('chores', 'last_completion_time')
    op.drop_column('chores', 'recurrence_value')
    op.drop_column('chores', 'recurrence_type')
    
    # Drop indexes from chore_visibility
    op.drop_index('idx_user_id_hidden', table_name='chore_visibility')
    op.drop_index('idx_chore_id', table_name='chore_visibility')
    
    # Drop chore_visibility table
    op.drop_table('chore_visibility')
