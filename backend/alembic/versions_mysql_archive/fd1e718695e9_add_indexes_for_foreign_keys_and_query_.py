"""add indexes for foreign keys and query optimization

Revision ID: fd1e718695e9
Revises: 1a4bc9866488
Create Date: 2025-06-23 01:36:17.552008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'fd1e718695e9'
down_revision: Union[str, None] = '1a4bc9866488'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_existing_indexes(connection, table_name):
    """Get list of existing index names for a table."""
    inspector = inspect(connection)
    indexes = inspector.get_indexes(table_name)
    return [idx['name'] for idx in indexes]


def upgrade() -> None:
    """Upgrade schema."""
    # Get connection to check existing indexes
    connection = op.get_bind()
    
    # Check existing indexes for users table
    user_indexes = get_existing_indexes(connection, 'users')
    
    # Check existing indexes for chores table
    chore_indexes = get_existing_indexes(connection, 'chores')
    
    # Add indexes only if they don't exist
    if 'idx_user_parent_id' not in user_indexes:
        op.create_index('idx_user_parent_id', 'users', ['parent_id'])
    
    if 'idx_chore_assignee_id' not in chore_indexes:
        op.create_index('idx_chore_assignee_id', 'chores', ['assignee_id'])
    
    if 'idx_chore_creator_id' not in chore_indexes:
        op.create_index('idx_chore_creator_id', 'chores', ['creator_id'])
    
    if 'idx_chore_status' not in chore_indexes:
        op.create_index('idx_chore_status', 'chores', ['is_completed', 'is_approved', 'is_disabled'])
    
    if 'idx_chore_created_at' not in chore_indexes:
        op.create_index('idx_chore_created_at', 'chores', ['created_at'])
    
    # The alter_column operations from auto-generation
    op.alter_column('chores', 'title',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255),
               nullable=False)
    op.alter_column('chores', 'description',
               existing_type=mysql.TEXT(collation='utf8mb4_unicode_ci'),
               nullable=False)
    op.alter_column('chores', 'reward',
               existing_type=mysql.FLOAT(),
               nullable=False)
    op.alter_column('chores', 'is_range_reward',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('chores', 'cooldown_days',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.alter_column('chores', 'is_recurring',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('chores', 'is_completed',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('chores', 'is_approved',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('chores', 'is_disabled',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('chores', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('chores', 'updated_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('chores', 'creator_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.alter_column('users', 'username',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
               nullable=False)
    op.alter_column('users', 'hashed_password',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255),
               nullable=False)
    op.alter_column('users', 'is_active',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)
    op.alter_column('users', 'is_parent',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Get connection to check existing indexes and foreign keys
    connection = op.get_bind()
    
    # For MySQL, we need to check if indexes are used by foreign keys
    # If they are, we cannot drop them
    
    # These custom indexes can always be dropped
    try:
        op.drop_index('idx_chore_created_at', 'chores')
    except:
        pass
        
    try:
        op.drop_index('idx_chore_status', 'chores')
    except:
        pass
    
    # For foreign key indexes, check if we can drop them
    # In MySQL, if an index is used by a foreign key, we cannot drop it
    # So we'll only drop indexes that we explicitly created and aren't auto-created
    
    # Get current indexes
    chore_indexes = get_existing_indexes(connection, 'chores')
    user_indexes = get_existing_indexes(connection, 'users')
    
    # Only drop if they exist and aren't the auto-generated FK indexes
    if 'idx_chore_creator_id' in chore_indexes and 'creator_id' in chore_indexes:
        # If both exist, we can drop our custom one
        try:
            op.drop_index('idx_chore_creator_id', 'chores')
        except:
            pass
    
    if 'idx_chore_assignee_id' in chore_indexes and 'assignee_id' in chore_indexes:
        # If both exist, we can drop our custom one
        try:
            op.drop_index('idx_chore_assignee_id', 'chores')
        except:
            pass
    
    if 'idx_user_parent_id' in user_indexes and 'parent_id' in user_indexes:
        # If both exist, we can drop our custom one
        try:
            op.drop_index('idx_user_parent_id', 'users')
        except:
            pass
    
    # Revert nullable changes
    op.alter_column('users', 'is_parent',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('users', 'is_active',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('users', 'hashed_password',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255),
               nullable=True)
    op.alter_column('users', 'username',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
               nullable=True)
    op.alter_column('chores', 'creator_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.alter_column('chores', 'updated_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('chores', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('chores', 'is_disabled',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('chores', 'is_approved',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('chores', 'is_completed',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('chores', 'is_recurring',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('chores', 'cooldown_days',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.alter_column('chores', 'is_range_reward',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True)
    op.alter_column('chores', 'reward',
               existing_type=mysql.FLOAT(),
               nullable=True)
    op.alter_column('chores', 'description',
               existing_type=mysql.TEXT(collation='utf8mb4_unicode_ci'),
               nullable=True)
    op.alter_column('chores', 'title',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=255),
               nullable=True)