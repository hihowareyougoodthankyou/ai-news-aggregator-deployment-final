"""Script to create database tables"""

import sys
from sqlalchemy import text
from app.database.database import engine
from app.database.models import Base


def create_tables(drop_existing: bool = False):
    """
    Create all database tables.
    
    Args:
        drop_existing: If True, drop all tables before creating (use when schema changed)
    """
    if drop_existing:
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        # Explicitly drop sources table (removed from models, so not in metadata)
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS sources CASCADE"))
            conn.commit()
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


if __name__ == "__main__":
    drop = "--drop" in sys.argv or "-d" in sys.argv
    create_tables(drop_existing=drop)
