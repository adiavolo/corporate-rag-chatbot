import sys
import os
from sqlalchemy import create_engine, text
from psycopg2 import sql, extensions, connect
from loguru import logger
from urllib.parse import urlparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

def create_database_if_not_exists():
    """
    Parses DATABASE_URL, connects to default 'postgres' db, and creates the target database if it doesn't exist.
    """
    url = urlparse(settings.DATABASE_URL)
    db_name = url.path[1:] # Remove leading slash
    
    # Construct default URL (connect to 'postgres' database)
    default_db_url = f"postgresql://{url.username}:{url.password}@{url.hostname}:{url.port}/postgres"
    
    logger.info(f"Checking if database '{db_name}' exists...")
    
    try:
        # We use psycopg2 directly for database creation because it requires autocommit mode
        # and SQLAlchemy engine.connect() inside transactions can be tricky for CREATE DATABASE
        conn = connect(
            dbname="postgres",
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Database '{db_name}' does not exist. Creating...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            logger.info(f"✅ Database '{db_name}' created successfully.")
        else:
            logger.info(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to check/create database: {e}")
        # Continue anyway, maybe it exists or user has to do it
        # Sometimes 'postgres' db is locked or different user permissions.

def init_schema():
    logger.info(f"Initializing schema for {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            # Read SQL file
            # Correct path handling
            script_path = os.path.join(os.path.dirname(__file__), "setup_db.sql")
            with open(script_path, "r") as f:
                sql_commands = f.read()
            
            logger.info("Executing setup_db.sql...")
            connection.execute(text(sql_commands))
            logger.info("✅ Database schema initialized successfully.")
            
    except Exception as e:
        logger.error(f"❌ Schema initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database_if_not_exists()
    init_schema()
