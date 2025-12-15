# Stage 1: Builder - Instalar dependencias
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    libpq-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install shared library
COPY shared/ /build/shared/
RUN pip install --no-cache-dir --user /build/shared

# Install app dependencies
COPY app/requirements.txt /build/
RUN pip install --no-cache-dir --user -r /build/requirements.txt

# Stage 2: Runtime - Imagen ligera sin compiladores
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only (PostgreSQL client lib)
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy shared module to runtime (ESTA LÍNEA FALTABA)
COPY shared/ /app/shared/

# Copy application code
COPY app/ /app/app/
COPY alembic.ini /app/
COPY app/migrations/ /app/app/migrations/

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')"

EXPOSE 8000

# Run migrations and start server
CMD python -m alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
