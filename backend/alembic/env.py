import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from backend.app.db.base import Base
target_metadata = Base.metadata


def get_url():
    """
    Get the DATABASE_URL with proper async driver.

    Uses the same URL conversion logic as the application to ensure
    consistency between app and migrations.

    Supports:
    - PostgreSQL (primary): postgresql+asyncpg://
    - MySQL (legacy): mysql+aiomysql://
    """
    from backend.app.core.config import settings
    return settings.DATABASE_URL


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with proper configuration."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare column types for better migration detection
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
        # Include schemas
        include_schemas=True,
        # Render item for PostgreSQL-specific types
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Run migrations in async 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
