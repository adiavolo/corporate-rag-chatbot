import sys
import os
from sqlalchemy import create_engine, text
from loguru import logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def reset_db():
    logger.info(f"Connecting to database: {settings.database.url}")
    try:
        engine = create_engine(settings.database.url, isolation_level="AUTOCOMMIT")
        with engine.connect() as connection:
            logger.info("⚠️ Wiping all data from tables...")
            
            # Truncate tables with CASCADE to handle foreign keys
            # documents -> chunks
            # lc_pg_collection -> lc_pg_embedding
            
            # We want to clear:
            # 1. documents (and thus chunks)
            # 2. lc_pg_embedding (vectors)
            # We can leave lc_pg_collection potentially, but cleaner to wipe it too if we want fresh start, 
            # though langchain might reuse the collection name.
            
            # 1. Drop Business Data Tables
            # We use DROP TABLE to ensure schema changes in setup_db.sql are applied upon re-init
            try:
                connection.execute(text("DROP TABLE IF EXISTS chunks CASCADE;"))
                connection.execute(text("DROP TABLE IF EXISTS documents CASCADE;"))
                logger.info("Dropped 'chunks' and 'documents' tables.")
            except Exception as e:
                logger.warning(f"Could not drop tables: {e}")

            # 2. Drop Vector Data Tables (if exists)
            try:
                connection.execute(text("DROP TABLE IF EXISTS lc_pg_embedding CASCADE;"))
                connection.execute(text("DROP TABLE IF EXISTS lc_pg_collection CASCADE;"))
                logger.info("Dropped 'lc_pg_embedding' and 'lc_pg_collection' tables.")
            except Exception:
                logger.info("Vector tables not found or empty (skipping).")
                
            logger.info("✅ Database reset complete.")
            
    except Exception as e:
        logger.error(f"❌ Reset failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all data? (y/n): ")
    if confirm.lower() == 'y':
        reset_db()
    else:
        print("Cancelled.")
