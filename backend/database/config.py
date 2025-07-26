"""Database configuration for SQLite"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Database URL - SQLite file in backend directory
DATABASE_URL = "sqlite+aiosqlite:///./ai_analyst.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True,
    pool_pre_ping=True,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Enable WAL mode for better concurrency
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and concurrency"""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set synchronous mode to NORMAL for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Set cache size (negative value means KB)
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        # Set temp store to memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
        logger.info("SQLite pragmas configured for optimal performance")

async def get_db_session():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def close_database():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")