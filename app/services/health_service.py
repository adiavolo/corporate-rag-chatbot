from datetime import datetime
from typing import Dict, Any
import time
from app.core.config import AppConfig
from app.core.schemas import HealthResponse
from app.clients.vector_client import VectorStore
from app.clients.llm_client import LLMClient
from app.data.repositories import DocumentRepository
from sqlalchemy import text
from loguru import logger

class HealthService:
    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: LLMClient,
        document_repo: DocumentRepository,
        config: AppConfig
    ):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.document_repo = document_repo
        self.config = config

    def get_system_status(self) -> HealthResponse:
        checks = {}
        
        # 1. Database
        checks['database'] = self._check_database()
        
        # 2. Vector Store
        checks['pgvector'] = self._check_vector_store()
        
        # 3. LLM
        checks['llm'] = self._check_llm()
        
        # Determine overall status
        statuses = [c['status'] for c in checks.values()]
        
        overall = "healthy"
        if "unhealthy" in statuses:
             overall = "unhealthy"
             # Refine logic: if only llm is down -> degraded?
             # User spec: "LLM down -> degraded", "Database down -> unhealthy"
             if checks['database']['status'] == "healthy" and checks['llm']['status'] == "unhealthy":
                 overall = "degraded"
        
        return HealthResponse(
            status=overall,
            components=checks,
            timestamp=datetime.now()
        )

    def _check_database(self) -> Dict[str, Any]:
        result = {"status": "unhealthy", "latency_ms": 0, "error": None}
        try:
            start = time.time()
            # Hack: access session from repo to run raw SQL
            self.document_repo.session.execute(text("SELECT 1"))
            result["latency_ms"] = (time.time() - start) * 1000
            result["status"] = "healthy"
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Health check DB failed: {e}")
        return result

    def _check_vector_store(self) -> Dict[str, Any]:
        result = {"status": "unhealthy", "latency_ms": 0, "error": None}
        try:
            start = time.time()
            if self.vector_store.check_health():
                result["status"] = "healthy"
            else:
                 result["error"] = "Health check returned false"
            result["latency_ms"] = (time.time() - start) * 1000
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Health check Vector failed: {e}")
        return result

    def _check_llm(self) -> Dict[str, Any]:
        result = {"status": "unhealthy", "latency_ms": 0, "error": None}
        try:
            start = time.time()
            if self.llm_client.check_health():
                 result["status"] = "healthy"
            else:
                 result["error"] = "Health check returned false"
            result["latency_ms"] = (time.time() - start) * 1000
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Health check LLM failed: {e}")
        return result
