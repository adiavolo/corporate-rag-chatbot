# Corporate RAG Chatbot

An enterprise-grade RAG system designed with a clean, layered architecture and deployed via Docker.

## 🚀 Quick Start (Docker)

The recommended way to run the application is using Docker Compose.

1.  **Configuration**:
    Create a `.env` file in the root directory (copy from `.env.example` if available) and set your API keys:
    ```env
    API_KEY=your_secret_key
    OPENROUTER_API_KEY=your_openrouter_key
    DATABASE_URL=postgresql://postgres:2310@db:5432/rag_db
    ```

2.  **Run**:
    ```bash
    docker-compose up --build
    ```

3.  **Access**:
    - **Frontend (UI)**: [http://localhost:7860](http://localhost:7860)
    - **Backend API**: [http://localhost:8000](http://localhost:8000)
    - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🏗️ Architecture

The project follows a **SOLID-compliant, layered architecture**:

-   **`app/api`**: REST API endpoints (FastAPI) handling requests and auth.
-   **`app/services`**: Business logic (RAG orchestration, retrieval, health checks).
-   **`app/clients`**: External integrations (LLM, Vector DB, Embeddings).
-   **`app/data`**: Database access layer (Repositories).
-   **`app/core`**: Configuration, schemas, and exceptions.
-   **`ui/`**: Gradio-based frontend interface.
-   **`scripts/`**: Database initialization and maintenance scripts.

## 🛠️ Tech Stack

-   **Backend**: FastAPI, Python 3.10
-   **Database**: PostgreSQL with `pgvector` extension
-   **AI/ML**: LangChain, SentenceTransformers, OpenRouter (LLM)
-   **Frontend**: Gradio
-   **Infrastructure**: Docker & Docker Compose

## 🧪 Development

To run locally without Docker (requires local PostgreSQL + pgvector):

1.  **Install**: `pip install -r requirements.txt`
2.  **Init DB**: `python scripts/init_db.py`
3.  **Run Backend**: `uvicorn app.main:app --reload`
4.  **Run Frontend**: `python ui/gradio_app.py`
