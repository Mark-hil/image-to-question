import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sql_app.db")

# For PostgreSQL, use:
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_size=5,
    max_overflow=10,
    poolclass=NullPool if "sqlite" in DATABASE_URL else None
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# For backward compatibility with sync code
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    raise ValueError("DATABASE_URL environment variable not set")
else:
    # Log the first 10 characters of the database URL (for security, don't log the whole thing)
    logger.info(f"Using database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL[:10]}...")

# Configure SQLAlchemy engine with connection pooling
try:
    logger.info("Initializing database engine...")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=300,    # Recycle connections after 5 minutes
        pool_size=5,         # Number of connections to keep open
        max_overflow=10,     # Max number of connections to create beyond pool_size
        echo=True            # Enable SQL logging
    )
    
    # Enable query logging
    log_queries()
    logger.info("Database engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database engine: {str(e)}")
    logger.error(traceback.format_exc())
    raise

try:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database session factory configured")
except Exception as e:
    logger.error(f"Failed to create session factory: {str(e)}")
    logger.error(traceback.format_exc())
    raise
Base = declarative_base()

def get_db():
    """Dependency for getting database session.
    
    Yields:
        Session: A database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
