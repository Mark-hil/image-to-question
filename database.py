import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
import time
import traceback

# Configure logging
logger = logging.getLogger(__name__)

def log_queries():
    @event.listens_for(engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, params, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug(f"Query: {statement}")
        if params:
            logger.debug(f"Params: {params}")

    @event.listens_for(engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, params, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        logger.debug(f"Query completed in {total:.3f} seconds")

# Configure logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()

# Get database URL from environment variables
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
