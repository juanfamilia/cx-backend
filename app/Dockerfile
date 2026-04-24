# syntax=docker/dockerfile:1
# Nota Railway: no usar RUN --mount=type=cache sin compatibilidad verificada; su builder puede
# rechazarlo ("missing an id argument"). La capa `uv sync` sigue cacheándose si no cambia uv.lock.

# --- Dependencias Python (capa cacheable; sin ffmpeg en build) ---
FROM python:3.13-slim AS builder

WORKDIR /app

# Sin esto, apt puede arrastrar recomendaciones enormes (p. ej. con ffmpeg: Mesa/GTK/SDL).
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Tras añadir dependencias en pyproject.toml: `uv lock` y commitear uv.lock
# (uv sync --frozen no instala paquetes que no figuran en el lock).
COPY pyproject.toml ./
COPY uv.lock ./

RUN uv sync --frozen --no-dev

# --- Runtime: solo lo necesario para ejecutar (ffmpeg + cliente libpq) ---
FROM python:3.13-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

COPY app/ ./app/
COPY alembic.ini ./
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

ENV PORT=8000
# Evita que `print()` y logs por stdout lleguen tarde al agregador de Railway (buffer sin TTY).
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
