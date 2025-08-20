"""add rejection reason field

Revision ID: f504e37553f9
Revises: 9df46904598b
Create Date: 2025-08-18 12:44:34.405650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f504e37553f9'
down_revision: Union[str, None] = '9df46904598b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rejection_reason field to chores table."""
    op.add_column('chores', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove rejection_reason field from chores table."""
    op.drop_column('chores', 'rejection_reason')
