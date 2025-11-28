# Dockerfile for Analysis Microservice (AI/ML)
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for ML (ffmpeg, audio libs, opencv)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install shared library
COPY shared/ /build/shared/
RUN pip install --no-cache-dir /build/shared

# Install analysis dependencies (includes ML libs)
COPY analysis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy analysis service code
COPY analysis/ /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8001}/health')"

EXPOSE 8001

# Start server (single worker for ML models in memory)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
