FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
COPY uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

# Copy application code
COPY app/ ./app/
COPY shared/ ./shared/
COPY alembic.ini ./
COPY Procfile ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Start command
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
