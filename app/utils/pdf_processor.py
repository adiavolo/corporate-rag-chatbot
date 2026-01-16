import io
import hashlib
from typing import Dict, Optional
import pypdf
from app.core.exceptions import IngestionError
from loguru import logger

def calculate_file_hash(file_bytes: bytes) -> str:
    """Generate SHA-256 hash for duplicate detection."""
    return hashlib.sha256(file_bytes).hexdigest()

def validate_pdf(file_bytes: bytes) -> bool:
    """Check if file appears to be a valid PDF."""
    if not file_bytes.startswith(b"%PDF"):
        return False
    try:
        io_bytes = io.BytesIO(file_bytes)
        pypdf.PdfReader(io_bytes)
        return True
    except Exception:
        return False

def extract_text_from_pdf(file_bytes: bytes) -> Dict[int, str]:
    """
    Extract text from PDF file.
    Returns: Dictionary mapping page_number (1-based) to text content.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_text = {}
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 10:
                pages_text[i + 1] = text.strip()
                
        if not pages_text:
            raise IngestionError("No extractable text found in PDF")
            
        return pages_text
    except Exception as e:
        logger.error(f"PDF Extraction failed: {e}")
        raise IngestionError(f"PDF Extraction failed: {e}")
