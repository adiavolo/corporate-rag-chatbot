from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from app.data.database import Document, Chunk
from app.core.exceptions import DatabaseError
from loguru import logger

class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, filename: str, document_hash: str, tag: str, uploaded_by: str, page_count: int) -> Document:
        try:
            doc = Document(
                filename=filename,
                document_hash=document_hash,
                tag=tag,
                uploaded_by=uploaded_by,
                page_count=page_count
            )
            self.session.add(doc)
            self.session.flush() # Flush to get ID, but let orchestrator commit
            return doc
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise DatabaseError(f"Failed to create document: {e}")

    def get_by_id(self, document_id: int) -> Optional[Document]:
        return self.session.query(Document).filter(Document.id == document_id).first()

    def get_by_hash(self, document_hash: str) -> Optional[Document]:
        return self.session.query(Document).filter(Document.document_hash == document_hash).first()

    def list_all(self, tag: Optional[str] = None) -> List[Document]:
        query = self.session.query(Document)
        if tag and tag != "*":
             query = query.filter(Document.tag == tag)
        return query.all()

    def delete(self, document_id: int) -> bool:
        try:
            doc = self.get_by_id(document_id)
            if doc:
                self.session.delete(doc)
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise DatabaseError(f"Failed to delete document: {e}")

class ChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_batch(self, chunks_data: List[Dict]) -> List[Chunk]:
        try:
            chunks = []
            for item in chunks_data:
                chunk = Chunk(
                    document_id=item['document_id'],
                    page_number=item['page_number'],
                    text=item['text']
                )
                self.session.add(chunk)
                chunks.append(chunk)
            self.session.flush()
            return chunks
        except Exception as e:
            logger.error(f"Failed to create chunks batch: {e}")
            raise DatabaseError(f"Failed to create chunks batch: {e}")

    def get_by_document(self, document_id: int) -> List[Chunk]:
        return self.session.query(Chunk)\
            .filter(Chunk.document_id == document_id)\
            .order_by(Chunk.page_number)\
            .all()

    def search_by_text(self, query: str, limit: int = 5, tag: Optional[str] = None) -> List[Chunk]:
        try:
            # Simple ILIKE search
            # If query is empty strings (from wildcard handling), we use "%" to match all
            term = query if query else ""
            search_pattern = f"%{term}%"
            
            q = self.session.query(Chunk).join(Document)
            
            if tag and tag.strip():
                 q = q.filter(Document.tag == tag)
                 
            return q.filter(Chunk.text.ilike(search_pattern))\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise DatabaseError(f"Keyword search failed: {e}")

    def delete_by_document(self, document_id: int) -> int:
        try:
            result = self.session.query(Chunk)\
                .filter(Chunk.document_id == document_id)\
                .delete(synchronize_session=False)
            self.session.flush()
            return result
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            raise DatabaseError(f"Failed to delete chunks: {e}")
