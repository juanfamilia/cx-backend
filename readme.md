# Siete CX Backend

## Project Specs

- Python 3.13
- PostgreSQL 14

## Siete InS (producto investigación)

API y modelo MVP documentados en [docs/SIETE_INS.md](docs/SIETE_INS.md) (`/api/v1/ins/...`).

## Migraciones DB

Con el mismo Python donde instalaste dependencias (`uv sync`, `pip install -e .`, etc.). Solo hace falta **`POSTGRES_URI`** en `.env` (Alembic no carga JWT/R2/OpenAI al migrar):

```bash
python -m alembic upgrade head
```
