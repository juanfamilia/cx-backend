FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies using uv sync (creates .venv)
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY alembic.ini ./

# Railway setea PORT; pon un default solo por si acaso
ENV PORT=8000
EXPOSE 8000

# Healthcheck interno del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# ⛔️ AQUÍ estaba el problema: estabas fijando 8000 en vez de usar $PORT
# Usa la forma *shell* para que se expanda $PORT
CMD /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
