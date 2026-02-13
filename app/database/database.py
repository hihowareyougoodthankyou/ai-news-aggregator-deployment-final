"""Database connection setup"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        Database connection URL
    """
    # Try DATABASE_URL first (Railway injects this when Postgres is linked)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Railway uses postgres:// but SQLAlchemy/psycopg2 expects postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Construct from individual components
    user = os.getenv('POSTGRES_USER', 'newsuser')
    password = os.getenv('POSTGRES_PASSWORD', 'newspass')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    dbname = os.getenv('POSTGRES_DB', 'news_aggregator')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


# Create engine
database_url = get_database_url()
engine = create_engine(
    database_url,
    poolclass=NullPool,  # Disable connection pooling for simplicity
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
