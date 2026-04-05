#!/bin/sh
set -e
cd /app

if [ "${SKIP_DB_MIGRATIONS:-}" = "1" ]; then
  echo "SKIP_DB_MIGRATIONS=1: omitiendo alembic upgrade head"
else
  echo "Aplicando migraciones (alembic upgrade head)..."
  /app/.venv/bin/alembic upgrade head
fi

echo "Iniciando uvicorn en puerto ${PORT:-8000}..."
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
