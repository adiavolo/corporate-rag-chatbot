import sys
import os
import psycopg2
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

def test_connection():
    print(f"Testing connection to: {settings.DATABASE_URL}")
    try:
        # Test 1: SQLAlchemy Connection
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ SQLAlchemy connection successful")
            
            # Test 2: pgvector extension
            result = connection.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector extension enabled")
            else:
                print("❌ pgvector extension NOT enabled")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if test_connection():
        sys.exit(0)
    else:
        sys.exit(1)
