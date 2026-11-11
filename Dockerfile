# Stage 1: Build React Frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend with uv, OCR & Poppler
FROM python:3.11-slim

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UPLOAD_DIR=/app/uploads \
    UV_PYTHON=/usr/local/bin/python3 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install system dependencies for OCR (Tesseract) and PDF rendering (Poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from uv.lock (leverage Docker cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and built frontend assets
COPY . .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create uploads directory and set permissions
RUN mkdir -p $UPLOAD_DIR && \
    chmod -R 777 $UPLOAD_DIR

# Expose the default port
EXPOSE 8000

# Health check (supports dynamic $PORT)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD sh -c "curl -f http://localhost:${PORT:-8000}/health || exit 1"

# Start FastAPI (supports dynamic $PORT on Railway, Render, Cloud Run, etc.)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
