# RAG Chatbot Architecture

## Overview
This project implements a Retrieval-Augmented Generation (RAG) chatbot using a layered, SOLID-compliant architecture. The system is designed for maintainability, testability, and separation of concerns.

## Layers

### 1. API Layer (`app/api`)
- **Responsibilities**: 
  - Handle HTTP Request/Response cycle.
  - Authentication (Bearer Token).
  - Dependency Injection (wiring services and repositories).
  - Validation of request schemas.
- **Key Components**: 
  - `routes.py`: FastAPI Router.
  - `dependencies.py`: Dependency providers.

### 2. Service Layer (`app/services`)
- **Responsibilities**: 
  - Orchestrate business logic.
  - Coordinate between Clients and Data layers.
  - Transaction handling (conceptually).
- **Key Components**:
  - `RAGService`: Main orchestrator for Chat, Ingest, and Retrieve workflows.
  - `IngestionService`: Handles PDF processing, chunking, and vector indexing.
  - `RetrievalService`: Implements search strategies (Vector + Keyword fallback).
  - `HealthService`: Aggregates system health status.

### 3. Client Layer (`app/clients`)
- **Responsibilities**: 
  - Abstract interactions with external systems.
- **Key Components**:
  - `LLMClient`: Interface for Language Models (OpenRouter implementation).
  - `EmbeddingClient`: Interface for Embedding Models (HuggingFace implementation).
  - `VectorStore`: Interface for Vector Database (PGVector implementation).

### 4. Data Layer (`app/data`)
- **Responsibilities**: 
  - Data persistence and retrieval from PostgreSQL.
  - Database schema definition.
- **Key Components**:
  - `repositories.py`: `DocumentRepository`, `ChunkRepository`.
  - `database.py`: SQLAlchemy models (`Document`, `Chunk`) and session management.

### 5. Core (`app/core`)
- **Responsibilities**: 
  - Cross-cutting concerns.
- **Key Components**:
  - `config.py`: Centralized Pydantic configuration.
  - `exceptions.py`: Custom exception hierarchy (`RAGException`).
  - `schemas.py`: Pydantic models for API contracts.

### 6. Utils (`app/utils`)
- **Responsibilities**: 
  - Pure, stateless helper functions.
- **Components**:
  - `pdf_processor.py`: PDF text extraction.
  - `text_splitter.py`: Text chunking logic.

## Request Flow

**Chat Request**:
User -> API (`/chat`) -> `RAGService.chat()` -> `RetrievalService.search()` -> `VectorStore` -> `RAGService` (build prompt) -> `LLMClient.generate()` -> User.

**Ingest Request**:
User -> API (`/ingest`) -> `RAGService.ingest()` -> `IngestionService.ingest_document()` -> `PDFUtils` -> `text_splitter` -> `ChunkRepository.create()` -> `EmbeddingClient.embed()` -> `VectorStore.add()` -> User.

## Extending the System
- **New Model**: Add a new config implementation or client adapter in `app/clients`.
- **New DB**: Implement `DocumentRepository` interface for new DB.
- **New Service**: Add service in `app/services` and register in `dependencies.py`.
