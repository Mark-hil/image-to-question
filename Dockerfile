# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UPLOAD_DIR=/app/uploads \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Set working directory
WORKDIR /app

# Install system dependencies only what's needed
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only essential files first (leverage Docker cache)
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -e . --no-deps

# Copy application code (exclude unnecessary files)
COPY --chown=app:app . .

# Create uploads directory and set permissions
RUN mkdir -p $UPLOAD_DIR && \
    chmod -R 755 $UPLOAD_DIR

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
