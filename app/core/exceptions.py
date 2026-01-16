from typing import Optional, Any, Dict

class RAGException(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

class IngestionError(RAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, error_code="INGESTION_ERROR", details=details)

class RetrievalError(RAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, error_code="RETRIEVAL_ERROR", details=details)

class LLMError(RAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, error_code="LLM_ERROR", details=details)

class DatabaseError(RAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR", details=details)

class ValidationError(RAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details=details)
