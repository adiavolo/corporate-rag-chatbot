# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for psycopg2/pgvector if compiling)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Torch CPU explicitly first to ensure we don't download the huge CUDA version
# This prevents OOM and disk space issues during build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY ui ./ui
COPY scripts ./scripts
COPY tests ./tests
COPY README.md .

# Create logs directory
RUN mkdir -p logs

# Environment variables to ensure python output is sent straight to terminal (e.g. your container log)
ENV PYTHONUNBUFFERED=1

# Default command (overridden in docker-compose)
CMD ["python", "app/main.py"]
