import base64
from typing import Dict
from app.core.config import IngestionConfig
from app.core.exceptions import IngestionError
from app.core.schemas import IngestResponse
from app.data.repositories import DocumentRepository, ChunkRepository
from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_client import VectorStore
from app.utils.pdf_processor import validate_pdf, extract_text_from_pdf, calculate_file_hash
from app.utils.text_splitter import split_text_into_chunks
from loguru import logger

class IngestionService:
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        config: IngestionConfig
    ):
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.config = config

    def ingest_document(self, file_bytes: bytes, filename: str, tag: str, uploaded_by: str) -> IngestResponse:
        """
        Orchestrate the complete ingestion pipeline.
        """
        doc_id = None
        try:
            logger.info(f"Starting ingestion for {filename} [{tag}]")

            # 1. Validate File
            if len(file_bytes) > self.config.max_file_size_bytes:
                raise IngestionError(f"File size exceeds limit of {self.config.max_file_size_mb}MB")
            
            if not validate_pdf(file_bytes):
                raise IngestionError("Invalid PDF file")
            
            # 2. Duplicate Check
            doc_hash = calculate_file_hash(file_bytes)
            existing = self.document_repo.get_by_hash(doc_hash)
            if existing:
                raise IngestionError(f"Document already exists (ID: {existing.id})")
                
            # 3. Extract Text
            pages_text = extract_text_from_pdf(file_bytes) # dict[page_num, text]
            
            # 4. Create Document Record
            # We commit later? Or now?
            # Ideally transaction. But for now we create record to get ID.
            # Services usually manage transaction scope if they own it.
            # But we passed in repositories which have a session.
            # We assume the session is active.
            
            doc = self.document_repo.create(
                filename=filename,
                document_hash=doc_hash,
                tag=tag,
                uploaded_by=uploaded_by,
                page_count=len(pages_text)
            )
            doc_id = doc.id
            logger.info(f"Created document record ID {doc_id}")

            # 5. Split and Chunk
            all_chunks_data = [] # For DB
            all_texts = []       # For embedding
            all_metadatas = []   # For vector store
            
            chunk_global_idx = 0
            
            for page_num, text in pages_text.items():
                chunks = split_text_into_chunks(text, self.config.chunk_size, self.config.chunk_overlap)
                
                for chunk_text in chunks:
                    all_chunks_data.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "text": chunk_text
                    })
                    
                    all_texts.append(chunk_text)
                    all_metadatas.append({
                        "document_id": doc_id,
                        "chunk_id": 0, # Placeholder, depends on DB insert?
                        "page_number": page_num,
                        "tag": tag,
                        "source": filename
                    })
                    chunk_global_idx += 1

            # 6. Store Chunks in DB
            created_chunks = self.chunk_repo.create_batch(all_chunks_data)
            
            # Commit the chunks to the database
            # Since create_batch only flushes, data is lost if we don't commit.
            # We must access the session from one of the repos to commit.
            self.chunk_repo.session.commit()
            
            # Update metadatas with actual chunk IDs
            for i, chunk in enumerate(created_chunks):
                all_metadatas[i]["chunk_id"] = chunk.id
            
            logger.info(f"Stored {len(created_chunks)} chunks in database")

            # 7. Generate Embeddings & Store in Vector DB
            if all_texts:
                logger.info("Generating embeddings...")
                vectors = self.embedding_client.embed_batch(all_texts)
                
                logger.info("Storing vectors...")
                self.vector_store.add_embeddings(vectors, all_texts, all_metadatas)

            # Return Response
            return IngestResponse(
                document_id=doc_id,
                filename=filename,
                chunks_created=len(created_chunks),
                status="success",
                pages_ingested=len(pages_text),
                tag=tag,
                uploaded_by=uploaded_by
            )

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            self._cleanup_on_failure(doc_id)
            if isinstance(e, IngestionError):
                raise e
            raise IngestionError(f"Ingestion process failed: {e}")

    def _cleanup_on_failure(self, doc_id: int):
        if doc_id:
            try:
                logger.warning(f"Cleaning up failed ingestion for document {doc_id}")
                self.document_repo.delete(doc_id)
                # Cleanup vector store?
                # Ideally yes, but VectorStore.delete_by_document might not be fully implemented.
                # Try it.
                self.vector_store.delete_by_document(doc_id)
            except Exception as cleanup_err:
                logger.error(f"Cleanup failed: {cleanup_err}")
