# 🏢 Corporate RAG Chatbot

![Status](https://img.shields.io/badge/Status-Active-success)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)

An enterprise-grade **Retrieval-Augmented Generation (RAG)** chatbot designed for querying internal corporate documents (HR Policies, Legal Contracts, Finance Reports). It uses **PostgreSQL with pgvector** for local vector storage and **OpenRouter** for LLM inference, ensuring data privacy and control.

---

## 🏗️ Architecture

The system consists of three main containerized services:

1.  **Frontend (`gradio_app.py`)**: A user-friendly web interface built with Gradio for uploading files, chatting, and debugging.
2.  **Backend (`app/main.py`)**: A FastAPI service that handles document processing, embedding generation, retrieval, and LLM communication.
3.  **Database (`PostgreSQL`)**: Stores document metadata, raw text chunks, and vector embeddings using the `pgvector` extension.

### Data Flow
1.  **Ingestion**: PDF → Text Extraction → Chunking (Semantic) → Embedding (MiniLM) → PGVector Storage.
2.  **Retrieval**: User Query → Embedding → Co-sine Similarity Search (PGVector) → Context Re-ranking.
3.  **Generation**: Context + Query → LLM (Llama 3 via OpenRouter) → Answer with Citations.

---

## 🚀 Features

*   **📄 Document Ingestion**: Upload PDFs with meta-tags (HR, Legal, Finance) and automatic duplicate detection (SHA-256 hashing).
*   **💬 RAG Chat Interface**: Context-aware answers with **page-level citations** and source transparency.
*   **🔍 Semantic Search & Debugger**: Visualize chunk retrieval, similarity scores, and inspect exactly what the AI 'sees' before answering.
*   **🩺 System Health Dashboard**: Real-time monitoring of Database, Vector Extension, Embedding Model, and API connectivity.
*   **🎨 Polished UI**: Custom-styled interface with high-contrast text for accessibility and a premium feel.

---

## 🛠️ Technology Stack

*   **Language**: Python 3.10+
*   **Web Framework**: FastAPI, Uvicorn
*   **UI Framework**: Gradio 5.x
*   **Database**: PostgreSQL 16 + `pgvector`
*   **AI/ML**:
    *   **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (Local, CPU-optimized)
    *   **LLM**: Meta Llama 3.2 (via OpenRouter API)
    *   **Orchestration**: LangChain

---

## 📋 Prerequisites

*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Recommended)
*   **OR** Python 3.10+ and PostgreSQL 16 installed locally.
*   An API Key from [OpenRouter.ai](https://openrouter.ai/).

---

## ⚙️ Configuration

Create a `.env` file in the root directory (one is provided by default).

```ini
# Database Config
POSTGRES_PASSWORD=2310
DATABASE_URL=postgresql://postgres:2310@db:5432/rag_db

# Keys
API_KEY=dev-secret-key-12345
OPENROUTER_API_KEY=your_key_here

# RAG Settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.25  # Lower threshold for better recall on varied docs
DEFAULT_TOP_K=5
```

> **Note**: The `SIMILARITY_THRESHOLD` is critical. If set too high (e.g., 0.6), the bot may reject valid answers saying "I don't have enough information."

---

## 🐳 Running with Docker (Recommended)

This is the fastest way to get started. It sets up the database, backend, and frontend automatically.

### 1. Start the Application
```bash
docker-compose up --build
```
*   *Step 1*: Builds the Python images.
*   *Step 2*: Starts PostgreSQL and initializes the `plpython3u` and `vector` extensions.
*   *Step 3*: Starts the Backend API (Port `8000`) and Gradio UI (Port `7860`).

### 2. Access the UI
Open your browser to:
👉 **[http://localhost:7860](http://localhost:7860)**

### 3. Stop the Application
To stop and remove containers (data persists in Docker volume):
```bash
docker-compose down
```

To stop and **wipe all data** (start fresh):
```bash
docker-compose down -v
```

---

## 📦 Manual Setup (Development)

If you strictly want to run without Docker:

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Setup Local Database**:
    Ensure you have a local Postgres instance running and update `.env` to point to `localhost`.
    ```bash
    python scripts/init_db.py
    ```
3.  **Run Backend**:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```
4.  **Run Frontend**:
    ```bash
    python ui/gradio_app.py
    ```

---

## 🕹️ Usage Guide

### 1. Uploading Documents
*   Go to the **Upload** tab.
*   Select a PDF file (e.g., "HR_Policy.pdf").
*   Choose a tag (e.g., **HR**) and enter your email.
*   Click **Upload**. You will see a success card with the number of pages processed.

### 2. Chatting
*   Go to the **Chat** tab.
*   Select the context **Tag** you want to chat with (e.g., HR).
*   Ask a question: *"What is the paternity leave policy?"*
*   The bot will answer and provide a **View Sources** dropdown to show exactly which pages were used.

### 3. Debugging / Semantic Search
*   If the bot says "I don't have enough info", go to the **Search** tab.
*   Enter your query or keywords.
*   The system will show you the raw chunks it found in the database and their **Similarity Score** (0 to 1).
    *   **Green**: High match (> 0.7)
    *   **Yellow**: Medium match (> 0.5)
    *   **Red**: Low match (< 0.5)

---

## ❓ Troubleshooting

**Q: The bot keeps saying "I don't have enough information".**
A: Check the **Search** tab specific query. If you see relevant chunks but they are Red/Yellow, your `SIMILARITY_THRESHOLD` in `.env` might be too high. We recommend `0.25` for broad matching.

**Q: The UI text is white/invisible.**
A: This was a known issue with the Dark Theme. It has been fixed in the latest build. Please run `docker-compose up --build` to apply the CSS patches.

**Q: Port 5432 is already in use.**
A: You likely have a local Postgres running. Either stop your local Postgres or change the mapped port in `docker-compose.yml`.
