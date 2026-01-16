import pytest
from unittest.mock import MagicMock
from app.core.schemas import SearchResult

def test_chat_success(rag_service, mock_llm_client):
    # Mock retrieval results
    search_result = SearchResult(
        text="Content page 1",
        score=0.9,
        page_number=1,
        document_name="test.pdf",
        document_id=1
    )
    rag_service.retrieval_service.search = MagicMock(return_value=[search_result])
    
    response = rag_service.chat("Question?", "HR", [])
    
    assert response.answer == "This is a mock answer."
    assert "test.pdf (Page 1)" in response.sources
    assert response.confidence == 0.9
    mock_llm_client.generate.assert_called_once()

def test_chat_no_results(rag_service):
    rag_service.retrieval_service.search = MagicMock(return_value=[])
    
    response = rag_service.chat("Question?", "HR")
    
    assert response.sources == []
    # Should still return an answer (LLM generates even with no context if prompt allows, or generic "I don't know")
    # Our prompt format: "Relevant Context: No relevant documents found."
    assert response.answer is not None

def test_chat_validation_error(rag_service):
    # Service catches exceptions and returns error message
    response = rag_service.chat("", "HR")
    assert response.confidence == 0.0
    assert "Question cannot be empty" in response.answer

def test_health_check(rag_service):
    response = rag_service.health()
    assert response.status == "healthy"
