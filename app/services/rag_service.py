from typing import List, Optional, Dict
from app.core.config import AppConfig
from app.core.exceptions import RAGException, ValidationError, RetrievalError
from app.core.schemas import ChatResponse, IngestResponse, SearchResponse, SearchResult, HealthResponse
from app.services.retrieval_service import RetrievalService
from app.services.ingestion_service import IngestionService
from app.services.health_service import HealthService
from app.clients.llm_client import LLMClient
from loguru import logger

class RAGService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        ingestion_service: IngestionService,
        health_service: HealthService,
        llm_client: LLMClient,
        config: AppConfig
    ):
        self.retrieval_service = retrieval_service
        self.ingestion_service = ingestion_service
        self.health_service = health_service
        self.llm_client = llm_client
        self.config = config

    def chat(self, question: str, tag: str, conversation_history: Optional[List[Dict]] = None) -> ChatResponse:
        """
        Main RAG output generation.
        """
        try:
            self._validate_question(question)
            
            # 1. Retrieve
            logger.info(f"RAG Chat: Retrieving for '{question}' in [{tag}]")
            search_results = self.retrieval_service.search(
                query=question, 
                tag=tag,
                top_k=self.config.retrieval.top_k, 
                threshold=self.config.retrieval.similarity_threshold
            )
            
            # 2. Build Prompt
            prompt = self._build_prompt(question, search_results, conversation_history)
            
            # 3. Generate
            logger.info("RAG Chat: Generating response from LLM")
            answer = self.llm_client.generate(prompt)
            
            # 4. Extract Sources
            sources = self._extract_sources(search_results)
            
            # Formulate response
            # Confidence currently a placeholder or we can calc from search scores
            avg_score = 0.0
            if search_results:
                avg_score = sum(r.score for r in search_results) / len(search_results)
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                confidence=avg_score
            )
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            # Ensure we return a valid response even on error
            return ChatResponse(
                answer=f"I encountered an error processing your request: {str(e)}",
                sources=[],
                confidence=0.0
            )

    def ingest(self, file_bytes: bytes, filename: str, tag: str, uploaded_by: str) -> IngestResponse:
        """
        Delegates document ingestion.
        """
        # IngestionService handles logic/errors
        return self.ingestion_service.ingest_document(file_bytes, filename, tag, uploaded_by)

    def retrieve(self, query: str, tag: str, top_k: Optional[int] = None) -> SearchResponse:
        """
        Delegates search/retrieve (for UI search tab).
        """
        try:
            results = self.retrieval_service.search(query, tag, top_k)
            return SearchResponse(results=results, total_results=len(results))
        except Exception as e:
             logger.error(f"Retrieve operation failed: {e}")
             # Return empty results
             return SearchResponse(results=[])

    def health(self) -> HealthResponse:
        return self.health_service.get_system_status()

    def _build_prompt(self, question: str, context: List[SearchResult], history: Optional[List[Dict]]) -> str:
        # 1. Format Context
        context_str = ""
        # Truncate context based on tokens (rough char count approx)
        max_chars = self.config.retrieval.max_context_tokens * 4 
        current_chars = 0
        
        for res in context:
            # Format: [Source Page X] Content
            snippet = f"[{res.document_name} Page {res.page_number}] {res.text}\n\n"
            if current_chars + len(snippet) > max_chars:
                break
            context_str += snippet
            current_chars += len(snippet)
        
        if not context_str:
            context_str = "No relevant documents found."

        # 2. Format History
        history_str = ""
        if history:
            # Take last 5 exchanges
            # assuming format [{"role": "user", "content": "..."}, ...]
            for msg in history[-5:]:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"

        # 3. Assemble
        prompt = f"""System: You are a helpful corporate assistant. Use the provided context to answer the question.
If the answer is not in the context, state that you don't know. Always cite the page numbers provided in the context.

Relevant Context:
{context_str}

Conversation History:
{history_str}

User Question: {question}

Assistant Answer:"""
        return prompt

    def _extract_sources(self, context: List[SearchResult]) -> List[str]:
        # Dedup sources: "Filename (Page X)"
        seen = set()
        sources = []
        for res in context:
            citation = f"{res.document_name} (Page {res.page_number})"
            if citation not in seen:
                sources.append(citation)
                seen.add(citation)
        return sources

    def _validate_question(self, question: str) -> None:
        if not question or not question.strip():
            raise ValidationError("Question cannot be empty")
        if len(question) > 1000:
            raise ValidationError("Question is too long (max 1000 chars)")
