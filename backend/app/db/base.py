from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Import all the models, so that Base has them before being
# imported by Alembic
from .base_class import Base  # noqa
from ..models.user import User  # noqa
from ..models.chore import Chore  # noqa
from ..models.family import Family  # noqa

# Create async engine with optimized connection pool settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # Connection pool settings
    pool_pre_ping=True,      # Test connections before using them
    pool_size=20,            # Increased pool size for better concurrency
    max_overflow=40,         # Allow more overflow connections during peak load
    pool_recycle=3600,       # Recycle connections after 1 hour (avoid MySQL timeouts)
    pool_timeout=60,         # Increased timeout for getting connection from pool
    connect_args={
        "server_settings": {
            "jit": "off"     # Disable JIT for more predictable performance
        },
        "command_timeout": 60,
    } if "postgresql" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
