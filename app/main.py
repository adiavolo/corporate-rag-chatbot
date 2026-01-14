import hashlib
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from app.config import settings
from app.auth import verify_token
from app.database import get_db, Document, Chunk
from app.pdf_processor import extract_text_from_pdf
from app.embeddings import get_embedding_service
from app.vectorstore import get_vector_store
from app.openrouter import openrouter_client
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger
import json

import sys
from fastapi import Request
import time
import uuid

# --- Logging Configuration ---
# Configure loguru to write to file with rotation and retention
logger.remove() # Remove default handler to avoid duplicates if re-imported
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    enqueue=True
)

app = FastAPI(title="Corporate RAG Chatbot")

@app.on_event("startup")
async def startup_event():
    logger.info("Startup: Loading embedding model...")
    get_embedding_service() # Forces initialization
    logger.info("Startup: Embedding model loaded.")

# --- Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log Request
    logger.info(f"[{request_id}] -> {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Log Response
        process_time = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] <- {response.status_code} (took {process_time:.2f}ms)")
        
        return response
    except Exception as e:
        logger.error(f"[{request_id}] !!! Exception: {e}")
        raise e

# --- Pydantic Schemas ---

class IngestResponse(BaseModel):
    document_id: int
    filename: str
    pages_ingested: int
    tag: str
    uploaded_by: str
    created_at: str

class RetrievalResult(BaseModel):
    chunk_id: Optional[int] = None
    document_id: int
    filename: Optional[str] = None
    page_number: int
    text: str
    similarity_score: float

class RetrievalResponse(BaseModel):
    query: str
    tag: str
    results: List[RetrievalResult]
    total_results: int
    message: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    tag: str

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    chunks_used: int
    model: str

class RetrieveRequest(BaseModel):
    query: str
    tag: str
    top_k: int = 5

class IngestRequest(BaseModel):
    filename: str
    tag: str
    base64_content: str
    uploaded_by: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    """
    Checks the health of all system components.
    """
    db_status = False
    embedding_status = False
    openrouter_status = False
    pgvector_status = False
    
    # 1. Database & pgvector
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_status = True
        
        res = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if res.fetchone():
            pgvector_status = True
        db.close()
    except Exception as e:
        logger.error(f"Health DB check failed: {e}")

    # 2. Embedding Model
    try:
        svc = get_embedding_service()
        # Verify it can run
        svc.embed_text("test")
        embedding_status = True
    except Exception as e:
        logger.error(f"Health Embedding check failed: {e}")

    # 3. OpenRouter
    openrouter_status = openrouter_client.check_health()

    status_code = 200 if all([db_status, embedding_status, openrouter_status, pgvector_status]) else 503
    
    return {
        "status": "healthy" if status_code == 200 else "unhealthy",
        "checks": {
            "database": db_status,
            "embedding_model": embedding_status,
            "openrouter": openrouter_status,
            "pgvector": pgvector_status
        },
        "timestamp": "Now" # You might want a real timestamp here
    }

@app.post("/ingest", status_code=status.HTTP_201_CREATED, response_model=IngestResponse)
def ingest_document(
    request: IngestRequest,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Ingests a PDF document.
    """
    logger.info(f"Starting ingestion for {request.filename}")
    
    # Validate Tag
    if request.tag not in settings.ALLOWED_TAGS_LIST:
        raise HTTPException(400, f"Invalid tag. Allowed: {settings.ALLOWED_TAGS_LIST}")

    # 1. Decode & Hash
    pdf_pages = extract_text_from_pdf(request.base64_content)
    # Re-encode specifically to hash the original content or hash the base64 string
    doc_hash = hashlib.sha256(request.base64_content.encode()).hexdigest()

    # Check duplicate
    existing = db.query(Document).filter(Document.document_hash == doc_hash).first()
    if existing:
        raise HTTPException(409, "Document already exists")

    # 2. Store Metadata (Business Data)
    new_doc = Document(
        filename=request.filename,
        document_hash=doc_hash,
        tag=request.tag,
        uploaded_by=request.uploaded_by,
        page_count=len(pdf_pages)
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 3. Store Chunks & Prepare for Vector Store
    texts = []
    metadatas = []

    for page in pdf_pages:
        chunk = Chunk(
            document_id=new_doc.id,
            page_number=page['page_number'],
            text=page['text']
        )
        db.add(chunk)
        db.commit() # Commit to get ID
        db.refresh(chunk)
        
        texts.append(page['text'])
        metadatas.append({
            "chunk_id": chunk.id,
            "tag": request.tag,
            "page_number": page['page_number'],
            "document_id": new_doc.id
        })

    # 4. Generate Embeddings (Langchain)
    vector_store = get_vector_store()
    vector_store.add_texts(texts=texts, metadatas=metadatas)
    
    return IngestResponse(
        document_id=new_doc.id,
        filename=new_doc.filename,
        pages_ingested=len(pdf_pages),
        tag=new_doc.tag,
        uploaded_by=new_doc.uploaded_by,
        created_at=str(new_doc.created_at)
    )

@app.post("/retrieve", response_model=RetrievalResponse)
def retrieve_documents(
    request: RetrieveRequest,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Retrieves documents based on query or wildcard.
    """
    if request.tag not in settings.ALLOWED_TAGS_LIST:
         raise HTTPException(400, f"Invalid tag. Allowed: {settings.ALLOWED_TAGS_LIST}")

    # Case 1: Wildcard "*"
    if request.query == "*":
        # Get all chunks for this tag from DB (Limit to reasonable amount for MVP, say 50)
        # Doing a join to get filename
        results = db.execute(text(f"""
            SELECT c.id, c.document_id, c.page_number, c.text, d.filename 
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.tag = :tag
            ORDER BY d.created_at DESC, c.page_number ASC
            LIMIT 50
        """), {"tag": request.tag}).fetchall()
        
        retrieval_results = []
        for r in results:
            retrieval_results.append(RetrievalResult(
                chunk_id=r.id,
                document_id=r.document_id,
                filename=r.filename,
                page_number=r.page_number,
                text=r.text,
                similarity_score=1.0 # Max score for explicit match
            ))
            
        return RetrievalResponse(
            query=request.query,
            tag=request.tag,
            results=retrieval_results,
            total_results=len(retrieval_results)
        )

    # Case 2: Semantic Search
    vector_store = get_vector_store()
    # Note: PGVector in langchain supports filter arguments for metadata
    # The filter syntax depends on the underlying driver, but usually key-value works for JSONB
    search_results = vector_store.similarity_search_with_score(
        query=request.query,
        k=request.top_k,
        filter={"tag": request.tag}
    )

    retrieval_results = []
    for doc, score in search_results:
        # Check threshold
        # Langchain PGVector with cosine strategy returns DISTANCE (0=same, 1=orthogonal, 2=opposite)
        # We want SIMILARITY (1=same, 0=orthogonal, -1=opposite)
        # Similarity = 1 - Distance
        
        similarity = 1 - score 
        
        if similarity < settings.SIMILARITY_THRESHOLD:
            continue
            
        # Enrich with filename if possible (could query DB, but maybe not critical for MVP speed)
        # We stored document_id in metadata
        doc_id = doc.metadata.get("document_id")
        fname = "Unknown"
        if doc_id:
            d = db.query(Document).filter(Document.id == doc_id).first()
            if d:
                fname = d.filename

        retrieval_results.append(RetrievalResult(
            chunk_id=doc.metadata.get("chunk_id"),
            document_id=doc.metadata.get("document_id"),
            filename=fname,
            page_number=doc.metadata.get("page_number"),
            text=doc.page_content,
            similarity_score=similarity
        ))
        
    return RetrievalResponse(
        query=request.query,
        tag=request.tag,
        results=retrieval_results,
        total_results=len(retrieval_results)
    )

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    RAG Chat endpoint.
    """
    logger.info(f"CHAT: Query='{request.query}' Tag='{request.tag}'")
    
    # 1. Retrieve
    # Re-use logic: call vector store directly
    vector_store = get_vector_store()
    search_results = vector_store.similarity_search_with_score(
        query=request.query,
        k=settings.DEFAULT_TOP_K,
        filter={"tag": request.tag}
    )
    logger.info(f"CHAT: Retrieved {len(search_results)} candidates from vector store.")
    
    context_text = ""
    sources = []
    chunks_used = 0
    seen_chunk_ids = set()
    doc_id_to_filename = {}

    # Helper to resolve filename
    def get_filename(doc_id):
        if doc_id in doc_id_to_filename:
            return doc_id_to_filename[doc_id]
        if not doc_id:
            return "Unknown"
        d = db.query(Document).filter(Document.id == doc_id).first()
        name = d.filename if d else "Unknown"
        doc_id_to_filename[doc_id] = name
        return name

    # Process Vector Results
    for doc, score in search_results:
        similarity = 1 - score
        logger.debug(f"Vector Candidate: page={doc.metadata.get('page_number')} sim={similarity:.4f}")
        
        if similarity >= settings.SIMILARITY_THRESHOLD:
            chunk_id = doc.metadata.get("chunk_id")
            if chunk_id and chunk_id not in seen_chunk_ids:
                page = doc.metadata.get("page_number", "?")
                doc_id = doc.metadata.get("document_id")
                fname = get_filename(doc_id)
                
                context_text += f"[{fname} Page {page}] {doc.page_content}\n\n"
                sources.append(f"{fname} (Page {page})")
                chunks_used += 1
                seen_chunk_ids.add(chunk_id)
        else:
             logger.debug(f"Skipped vector candidate due to low similarity.")

    # 1b. Fallback: Keyword Search (Hybrid-ish)
    if chunks_used < settings.DEFAULT_TOP_K:
        logger.info("CHAT: Attempting Keyword Fallback...")
        kw_sql = text("""
            SELECT c.id, c.page_number, c.text, c.document_id 
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.tag = :tag AND c.text ILIKE :query
            LIMIT 5
        """)
        
        like_query = f"%{request.query.strip()}%"
        
        try:
            kw_results = db.execute(kw_sql, {"tag": request.tag, "query": like_query}).fetchall()
            for r in kw_results:
                if r.id not in seen_chunk_ids:
                    fname = get_filename(r.document_id)
                    context_text += f"[{fname} Page {r.page_number}] {r.text}\n\n"
                    sources.append(f"{fname} (Page {r.page_number})")
                    chunks_used += 1
                    seen_chunk_ids.add(r.id)
                    logger.info(f"CHAT: Added Keyword Match from {fname} Page {r.page_number}")
                    if chunks_used >= settings.DEFAULT_TOP_K * 2: 
                        break
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")

    unique_sources = sorted(list(set(sources)))
    
    if not context_text:
        return ChatResponse(
            query=request.query,
            answer=f"I don't have enough information in the {request.tag} documents to answer this question.",
            sources=[],
            chunks_used=0,
            model=settings.LLM_MODEL
        )

    # 2. Format Prompt
    prompt = f"""You are a helpful corporate document assistant.
Answer the question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information."
Always cite the page number(s) where you found the information.

Context:
{context_text}

Question: {request.query}

Answer:"""

    # 3. Call LLM
    answer = openrouter_client.chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )
    
    return ChatResponse(
        query=request.query,
        answer=answer,
        sources=unique_sources,
        chunks_used=chunks_used,
        model=settings.LLM_MODEL
    )
