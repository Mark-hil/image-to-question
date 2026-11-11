import os
from typing import AsyncGenerator, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qs
import ssl as _ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from config import settings
import logging
import asyncio
from sqlalchemy import text


logger = logging.getLogger(__name__)

# Read DB URL from environment (default to sqlite async for local dev)
_raw_db_url = settings.DATABASE_URL

# If a plain `postgresql://` URL is provided, SQLAlchemy's async extension
# requires the URL to specify an async driver such as `asyncpg`:
#   postgresql+asyncpg://user:pass@host/db
# Normalize common postgres URLs to use asyncpg automatically.
if _raw_db_url.startswith("postgres://"):
    DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgresql://") and "+" not in _raw_db_url:
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

# Add timeout configurations to connect_args for asyncpg
if "postgresql" in DATABASE_URL:
    connect_args.update({
        "server_settings": {
            "application_name": "question_gen_app"
        },
        "command_timeout": 30
    })

engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": connect_args,
}

if "sqlite" in DATABASE_URL:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_timeout"] = 30

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

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

def _format_column_default(col, dialect) -> Optional[str]:
    """Return a SQL DEFAULT expression for a column when adding it to an existing table."""
    if col.server_default is not None:
        arg = col.server_default.arg
        if hasattr(arg, "text"):
            return str(arg.text)
        if hasattr(arg, "compile"):
            return str(arg.compile(dialect=dialect))
        return str(arg)
    if col.default is not None and col.default.is_scalar:
        val = col.default.arg
        if isinstance(val, bool):
            return ("true" if val else "false") if dialect.name == "postgresql" else ("1" if val else "0")
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            escaped = val.replace("'", "''")
            return f"'{escaped}'"
    return None


def _sync_missing_columns(sync_conn) -> None:
    """Inspect existing tables and add any columns defined on ORM models that are missing in the DB."""
    from sqlalchemy import inspect

    inspector = inspect(sync_conn)
    dialect = sync_conn.dialect
    preparer = dialect.identifier_preparer
    existing_tables = set(inspector.get_table_names())

    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue

        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        quoted_table = preparer.quote(table_name)

        for col in table.columns:
            if col.name in existing_cols:
                continue

            col_type = col.type.compile(dialect=dialect)
            quoted_col = preparer.quote(col.name)
            default_expr = _format_column_default(col, dialect)

            ddl = f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_col} {col_type}"
            if default_expr is not None:
                ddl += f" DEFAULT {default_expr}"
                if not col.nullable:
                    ddl += " NOT NULL"

            sync_conn.execute(text(ddl))
            logger.info(f"Added missing column '{col.name}' ({col_type}) to table '{table_name}'")

        existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
        for idx in table.indexes:
            if idx.name and idx.name not in existing_indexes:
                idx.create(sync_conn, checkfirst=True)
                logger.info(f"Created missing index '{idx.name}' on table '{table_name}'")


async def init_db() -> None:
    """Create database tables with retry logic and automatic column synchronization."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to initialize database (attempt {attempt + 1}/{max_retries})")
            
            # Test connection first
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                
            # Create tables and add any missing columns on existing tables
            import models  # noqa: F401
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await conn.run_sync(_sync_missing_columns)
                logger.info("✅ Database tables created/migrated successfully")
                return
                
        except asyncio.TimeoutError as e:
            logger.error(f"Database connection timeout (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Database initialization failed.")
                raise
                
        except Exception as e:
            logger.error(f"Database initialization error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached. Database initialization failed.")
                raise

