import pytest
from app.core.exceptions import IngestionError
import base64

def test_ingest_success(ingestion_service, mock_document_repo, mock_chunk_repo, mock_vector_store):
    # Valid PDF signature
    valid_pdf = b"%PDF-1.4\nTest PDF Content that looks valid enough for simple check"
    # Actually our valid_pdf check uses pypdf, so we need a real header or mock the validation.
    # It implies pypdf.PdfReader must work. 
    # Let's mock the utils instead of creating real PDF bytes, to allow simple testing.
    
    # We will mock app.utils.pdf_processor in the test file context?
    # Or cleaner: The IngestionService imports it. We can patch it.
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.ingestion_service.validate_pdf", lambda x: True)
        mp.setattr("app.services.ingestion_service.calculate_file_hash", lambda x: "hash123")
        mp.setattr("app.services.ingestion_service.extract_text_from_pdf", lambda x: {1: "page 1 text"})
        
        response = ingestion_service.ingest_document(valid_pdf, "doc.pdf", "HR", "user")
        
        assert response.status == "success"
        assert response.document_id == 1
        
        mock_document_repo.create.assert_called_once()
        mock_chunk_repo.create_batch.assert_called_once()
        mock_vector_store.add_embeddings.assert_called_once()

def test_ingest_duplicate_error(ingestion_service, mock_document_repo):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.ingestion_service.validate_pdf", lambda x: True)
        mp.setattr("app.services.ingestion_service.calculate_file_hash", lambda x: "hash123")
        
        from app.data.database import Document
        mock_document_repo.get_by_hash.return_value = Document(id=99, filename="old.pdf")
        
        with pytest.raises(IngestionError) as exc:
            ingestion_service.ingest_document(b"content", "new.pdf", "HR", "user")
        
        assert "already exists" in str(exc.value)
