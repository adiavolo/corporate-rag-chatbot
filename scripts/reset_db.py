import sys
import os
from sqlalchemy import create_engine, text
from loguru import logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

def reset_db():
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
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
            
            # 1. Clear Business Data
            try:
                connection.execute(text("TRUNCATE TABLE documents CASCADE;"))
                logger.info("Cleared 'documents' and 'chunks' tables.")
            except Exception as e:
                logger.warning(f"Could not truncate documents: {e}")

            # 2. Clear Vector Data (if exists)
            try:
                connection.execute(text("TRUNCATE TABLE lc_pg_embedding CASCADE;"))
                logger.info("Cleared 'lc_pg_embedding' table.")
            except Exception:
                logger.info("Table 'lc_pg_embedding' not found or empty (skipping).")
                
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
