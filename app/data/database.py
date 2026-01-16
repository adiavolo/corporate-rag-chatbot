from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from contextlib import contextmanager
from app.core.config import settings
from app.core.exceptions import DatabaseError

# Database URL
SQLALCHEMY_DATABASE_URL = settings.database.url

# Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=5, max_overflow=10)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base Model
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    document_hash = Column(String(64), unique=True, nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    uploaded_by = Column(String(100), nullable=False)
    page_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    # Added created_at to match user request "created_at (timestamp)" in Chunk model desc
    # Though original didn't have it clearly shown in model, typically chunks created same time as doc.
    created_at = Column(DateTime, default=func.now()) 

    document = relationship("Document", back_populates="chunks")

def get_db_session() -> Session:
    return SessionLocal()

@contextmanager
def db_session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Database session failed: {e}")
    finally:
        session.close()

# Keep get_db for FastAPI dependency if needed later, but Services uses repositories
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
