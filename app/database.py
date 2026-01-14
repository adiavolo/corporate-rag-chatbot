from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import settings

# Database URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

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

    document = relationship("Document", back_populates="chunks")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
