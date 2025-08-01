"""add reward adjustments table

Revision ID: 09d5bdf0cd1e
Revises: fd1e718695e9
Create Date: 2025-08-01 02:33:31.638012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09d5bdf0cd1e'
down_revision: Union[str, None] = 'fd1e718695e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create reward_adjustments table
    op.create_table('reward_adjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['child_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], )
    )
    
    # Create indexes for foreign keys and query optimization
    op.create_index('idx_child_adjustments', 'reward_adjustments', ['child_id'])
    op.create_index('idx_parent_adjustments', 'reward_adjustments', ['parent_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table (this will automatically drop indexes and foreign keys)
    op.drop_table('reward_adjustments')
