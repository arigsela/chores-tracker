"""Add created_at and updated_at to users table

Revision ID: a988bdaeacef
Revises: f495eb296fbb
Create Date: 2025-08-27 12:52:43.945275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a988bdaeacef'
down_revision: Union[str, None] = 'f495eb296fbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add timestamp columns to users table
    op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove timestamp columns from users table
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
