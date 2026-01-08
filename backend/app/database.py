"""
Database configuration and session management

This module handles SQLAlchemy setup including:
- Database engine configuration
- Session management for async operations
- Database initialization and health checks
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine, text
from typing import AsyncGenerator
import asyncio

from app.config import settings

# Database engines
async_engine = None
sync_engine = None
AsyncSessionLocal = None
SessionLocal = None

class Base(DeclarativeBase):
    """Base model class for all database models."""
    pass

async def get_async_engine():
    """Get async database engine instance."""
    global async_engine
    if async_engine is None:
        # Convert sync database URL to async if needed
        database_url = settings.database_url
        if database_url.startswith("sqlite:"):
            database_url = database_url.replace("sqlite:", "sqlite+aiosqlite:")
        elif database_url.startswith("postgresql:"):
            database_url = database_url.replace("postgresql:", "postgresql+asyncpg:")
        
        async_engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            future=True,
            pool_pre_ping=True,  # Verify connections before use
        )
    return async_engine

def get_sync_engine():
    """Get synchronous database engine for migrations."""
    global sync_engine
    if sync_engine is None:
        sync_engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            future=True,
            pool_pre_ping=True,
        )
    return sync_engine

async def get_async_session_maker():
    """Get async session maker."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        engine = await get_async_engine()
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return AsyncSessionLocal

def get_sync_session_maker():
    """Get synchronous session maker for migrations."""
    global SessionLocal
    if SessionLocal is None:
        engine = get_sync_engine()
        SessionLocal = sessionmaker(
            engine,
            autoflush=False,
            autocommit=False,
        )
    return SessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Use this in FastAPI endpoints with Depends(get_db).
    """
    session_maker = await get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables."""
    from app.models import user, project, article, search_cache  # Import all models
    
    engine = await get_async_engine()
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables initialized")

async def drop_db() -> None:
    """Drop all database tables (use with caution!)."""
    from app.models import user, project, article, search_cache  # Import all models
    
    engine = await get_async_engine()
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
    
    print("⚠️  All database tables dropped")

async def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        engine = await get_async_engine()
        async with engine.begin() as conn:
            # Try a simple query
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def get_db_info() -> dict:
    """Get database information for health checks."""
    try:
        engine = await get_async_engine()
        async with engine.begin() as conn:
            # Get database version info
            if "sqlite" in settings.database_url:
                result = await conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                db_type = "SQLite"
            elif "postgresql" in settings.database_url:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()[0].split()[1]
                db_type = "PostgreSQL"
            else:
                db_type = "Unknown"
                version = "Unknown"
            
            return {
                "connected": True,
                "database_type": db_type,
                "version": version,
                "url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "local",
                "echo": settings.database_echo
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "database_type": "Unknown",
            "version": "Unknown"
        }

# Database event handlers
async def startup_db():
    """Database startup handler."""
    print("🔄 Initializing database connection...")
    
    # Test connection
    if await check_db_connection():
        print("✅ Database connection established")
    else:
        print("❌ Database connection failed")
        raise Exception("Failed to connect to database")
    
    # Initialize tables if they don't exist
    if settings.debug:
        # In development, create tables automatically
        await init_db()

async def shutdown_db():
    """Database shutdown handler."""
    global async_engine, sync_engine
    
    print("🔄 Closing database connections...")
    
    if async_engine:
        await async_engine.dispose()
        async_engine = None
    
    if sync_engine:
        sync_engine.dispose()
        sync_engine = None
    
    print("✅ Database connections closed")