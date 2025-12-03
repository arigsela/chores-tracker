"""Add approval_reward field to chores table

Revision ID: 9df46904598b
Revises: 09d5bdf0cd1e
Create Date: 2025-08-17 22:26:56.239821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9df46904598b'
down_revision: Union[str, None] = '09d5bdf0cd1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only add the approval_reward column to chores table
    op.add_column('chores', sa.Column('approval_reward', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the approval_reward column from chores table
    op.drop_column('chores', 'approval_reward')
