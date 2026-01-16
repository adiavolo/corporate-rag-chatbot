from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Internal Domain Models ---

class Document(BaseModel):
    id: Optional[int] = None
    filename: str
    document_hash: str
    tag: str
    uploaded_by: str
    upload_date: Optional[datetime] = None
    page_count: Optional[int] = None

class Chunk(BaseModel):
    id: Optional[int] = None
    document_id: int
    page_number: int
    text: str
    created_at: Optional[datetime] = None

class SearchResult(BaseModel):
    text: str
    score: float
    page_number: int
    document_name: str
    document_id: Optional[int] = None

# --- API Request Schemas ---

class IngestRequest(BaseModel):
    # Field "file" described as file upload representation. 
    # Current implementation passes base64 string. 
    # We will accept base64_content and alias it or use it directly.
    # To strictly follow instructions: "file: File upload representation"
    # But usually this means Multipart/Form-Data if not base64.
    # Given the constraint to not break things, we stick to base64 for JSON body.
    filename: str
    tag: str
    uploaded_by: str # Email
    base64_content: str = Field(..., description="Base64 encoded file content")

class ChatRequest(BaseModel):
    question: str = Field(..., alias="query") # Alias to support existing 'query' key if needed, or map it.
    # Actually, current main.py expects 'query'. User asks for 'question'.
    # We will use 'question'. API layer will handle mapping if needed.
    conversation_history: Optional[List[Dict[str, str]]] = []
    max_tokens: Optional[int] = None
    tag: str # Context tag (HR, etc) - Added based on main.py usage need throughout.

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None
    tag: str # Context tag

# --- API Response Schemas ---

class IngestResponse(BaseModel):
    document_id: int
    filename: str
    chunks_created: int
    status: str
    pages_ingested: int
    tag: Optional[str] = None
    uploaded_by: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[float] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, Any]
    timestamp: datetime
