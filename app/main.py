import time
import uuid
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.exceptions import RAGException
from app.api.routes import router as api_router
from app.api.dependencies import get_embedding_client

# --- Logging Configuration ---
# Configure loguru to write to file with rotation and retention
logger.remove() # Remove default handler to avoid duplicates if re-imported
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    enqueue=True
)

app = FastAPI(
    title="Corporate RAG Chatbot",
    description="Upgraded architecture with SOLID principles",
    version="2.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log Request
    logger.info(f"[{request_id}] -> {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Log Response
        process_time = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] <- {response.status_code} (took {process_time:.2f}ms)")
        
        return response
    except Exception as e:
        logger.error(f"[{request_id}] !!! Exception: {e}")
        raise e

# --- Exception Handlers ---
@app.exception_handler(RAGException)
async def handle_rag_exception(request: Request, exc: RAGException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        },
    )

# --- Routes ---
# Mount the API router
# Note: Old app had routes at root (e.g. /chat). 
# New structure usually puts them under /api/v1.
# But "Preserve existing functionality" means preserving URL paths if possible to not break UI.
# Validating: Docker UI calls `/ingest`, `/chat`, `/retrieve` at root?
# Let's check `ui/gradio_app.py`.
# It uses `API_URL = "http://localhost:8000"`.
# And calls `f"{API_URL}/ingest"`.
# So we MUST mount at root or root-level.
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Corporate RAG Chatbot API", "version": "2.0.0", "status": "running"}

# --- Startup/Shutdown ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated.")
    
    # 1. Load Embedding Model (Pre-warm)
    try:
        logger.info("Pre-loading embedding model...")
        # Get singleton to trigger load
        get_embedding_client(settings)
        logger.info("Embedding model loaded.")
    except Exception as e:
        logger.warning(f"Embedding model pre-load warning (non-fatal): {e}")

    # 2. Database Check?
    # Repositories check on first use.
    # We could add explicit check here but HealthService covers it.
    
    logger.info("Application ready to serve requests.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
