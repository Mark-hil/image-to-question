import os
from typing import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit, parse_qs
import ssl as _ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Read DB URL from environment (default to sqlite async for local dev)
_raw_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sql_app.db")

# If a plain `postgresql://` URL is provided, SQLAlchemy's async extension
# requires the URL to specify an async driver such as `asyncpg`:
#   postgresql+asyncpg://user:pass@host/db
# Normalize common postgres URLs to use asyncpg automatically.
if _raw_db_url.startswith("postgresql://") and "+" not in _raw_db_url:
    DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgresql+psycopg2://"):
    DATABASE_URL = _raw_db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw_db_url

logger.info(f"Using DATABASE_URL: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL[:30]}...")

# Prepare connect_args and strip unsupported query params (e.g., sslmode) for asyncpg
connect_args = {}
parsed = urlsplit(DATABASE_URL)
qs = parse_qs(parsed.query)
if qs:
    # If sslmode is present (common with some cloud providers), asyncpg.connect
    # doesn't accept `sslmode` as a kwarg. Provide an SSLContext instead and
    # remove the query parameters from the DSN so they are not forwarded.
    if 'sslmode' in qs or 'ssl' in qs or 'channel_binding' in qs:
        ctx = _ssl.create_default_context()
        # Require certificate verification by default; change if you need different behavior
        connect_args['ssl'] = ctx

    # Rebuild DATABASE_URL without the query string so asyncpg won't receive unknown kwargs
    if parsed.query:
        DATABASE_URL = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    poolclass=NullPool if "sqlite" in DATABASE_URL else None,
    connect_args=connect_args or None,
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db() -> None:
    """Create database tables (runs synchronously in a thread via run_sync)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

