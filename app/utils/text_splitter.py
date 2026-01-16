from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

def clean_text(text: str) -> str:
    """
    Remove excessive whitespace and normalize text.
    """
    return " ".join(text.split())

def split_text_into_chunks(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Divide long text into smaller chunks using recursive character splitting.
    """
    # Use config values if not provided
    # Note: accessing settings inside utility is okay, but purely functional is better.
    # We'll use defaults from config if None.
    size = chunk_size or settings.ingestion.chunk_size
    overlap = chunk_overlap or settings.ingestion.chunk_overlap

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    return text_splitter.split_text(text)
