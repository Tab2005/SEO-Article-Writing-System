"""
Database Configuration and Session Management.

Provides async database connection and session handling.
Supports both SQLite (local development) and PostgreSQL (production).
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def get_async_database_url(url: str) -> str:
    """
    Convert database URL to async version.
    
    - SQLite: sqlite:// -> sqlite+aiosqlite://
    - PostgreSQL: postgresql:// -> postgresql+asyncpg://
    """
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Get database URL
async_database_url = get_async_database_url(settings.database_url)

# Check if using SQLite
is_sqlite = "sqlite" in settings.database_url

# Create async engine with appropriate settings
if is_sqlite:
    # SQLite settings (no pool)
    engine = create_async_engine(
        async_database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL settings (with pool)
    engine = create_async_engine(
        async_database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
