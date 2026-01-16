-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    document_hash VARCHAR(64) UNIQUE NOT NULL,
    tag VARCHAR(50) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    page_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_tag ON documents(tag);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(document_hash);

-- Chunks Table
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

-- Note: Langchain tables (lc_pg_collection, lc_pg_embedding) are created automatically by the library
