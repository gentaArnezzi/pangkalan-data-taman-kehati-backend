from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from typing import AsyncGenerator
import os
from dotenv import load_dotenv
from .models import Base
from .utils.logging_config import get_logger

logger = get_logger(__name__)

load_dotenv()

# Check for ASYNC_DATABASE_URL first, fall back to DATABASE_URL
async_database_url = os.getenv("ASYNC_DATABASE_URL")
raw_database_url = async_database_url or os.getenv("DATABASE_URL")

if not raw_database_url:
    raise ValueError("Either ASYNC_DATABASE_URL or DATABASE_URL environment variable must be set")

# Ensure we always use the async driver (psycopg v3) for async operations
if not "+psycopg" in raw_database_url:
    if "://" in raw_database_url and "+" not in raw_database_url.split("://")[0]:
        # Convert to psycopg async driver
        parts = raw_database_url.split("://", 1)
        raw_database_url = f"{parts[0]}+psycopg://{parts[1]}"

DATABASE_URL = raw_database_url

# Create async engine
logger.info("Initializing database engine with URL: %s", DATABASE_URL.replace('@', '***@'))
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "False").lower() == "true",  # Only enable in development
    pool_pre_ping=True,
    pool_size=10,  # Increased pool size for better performance
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections every hour
    pool_timeout=30,  # Set connection timeout
    pool_reset_on_return='commit',  # Reset connections on return
    connect_args={
        "application_name": "taman-kehati-api",
        "connect_timeout": 10,  # Set connection timeout
    }
)
logger.info("Database engine initialized successfully")

# Create async session
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables"""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully")


# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    logger.debug("Creating new database session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")