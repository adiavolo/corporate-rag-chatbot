import io
import base64
from typing import List, Dict, Any
import pypdf
from loguru import logger
from app.config import settings

from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(base64_content: str) -> List[Dict[str, Any]]:
    """
    Decodes PDF, extracts text, and creates semantic chunks with overlap.
    """
    try:
        # Decode base64
        pdf_bytes = base64.b64decode(base64_content)
        
        if len(pdf_bytes) > settings.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB")

        # Read PDF
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        raw_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 10:
                raw_pages.append({
                    "page_number": i + 1,
                    "text": text.strip()
                })
        
        if not raw_pages:
            raise ValueError("No text found in PDF")

        # Intelligent Chunking
        # Use smaller chunks (500 chars) to capture specific policy clauses (e.g. "Maternity Leave") 
        # without diluting them with unrelated text.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, 
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        final_chunks = []
        
        for page in raw_pages:
            # We split PER PAGE to keep the page number reference accurate
            # Ideally we would merge across pages but keeping page citation is a hard constraint for this MVP
            chunks = text_splitter.split_text(page["text"])
            
            for chunk_text in chunks:
                final_chunks.append({
                    "page_number": page["page_number"],
                    "text": chunk_text
                })
                
        logger.info(f"Split {len(raw_pages)} pages into {len(final_chunks)} semantic chunks")
        return final_chunks

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise e
