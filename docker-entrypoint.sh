#!/bin/sh
set -e
cd /app

echo "[entrypoint] $(date -u +%Y-%m-%dT%H:%M:%SZ) cwd=$(pwd) PORT=${PORT:-8000}"

if [ "${SKIP_DB_MIGRATIONS:-}" = "1" ]; then
  echo "SKIP_DB_MIGRATIONS=1: omitiendo alembic upgrade head"
else
  echo "Aplicando migraciones (alembic upgrade head)..."
  /app/.venv/bin/alembic upgrade head
  echo "[entrypoint] $(date -u +%Y-%m-%dT%H:%M:%SZ) migraciones listas"
fi

echo "[entrypoint] $(date -u +%Y-%m-%dT%H:%M:%SZ) iniciando uvicorn 0.0.0.0:${PORT:-8000}"
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
