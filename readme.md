# Siete CX Backend

API principal del **ecosistema Siete Inteligencia Creativa** (inteligencia aplicada a investigación, experiencia y operación): **Field**, **CX**, **InS**, **Clever**, **Perfil** — sobre **FastAPI** + **PostgreSQL**. Visión de producto y continuidad PRE-FIELD ↔ FIELD: [`docs/7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md`](docs/7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md). Tenant, flags y contrato compartido: [`docs/ECOSYSTEM_SIETE.md`](docs/ECOSYSTEM_SIETE.md), [`docs/SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md`](docs/SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md).

## Project Specs

- Python 3.13
- PostgreSQL 14
- FastAPI (`app/main.py`)

## Siete InS (producto investigación)

API y modelo MVP documentados en [docs/SIETE_INS.md](docs/SIETE_INS.md) (`/api/v1/ins/...`).

## Ecosistema (tenant, sub-tenant, Field)

[docs/ECOSYSTEM_SIETE.md](docs/ECOSYSTEM_SIETE.md) — `end_clients`, flags Field/Clever, `GET /entitlements/me`.

## Migraciones DB

Con el mismo Python donde instalaste dependencias (`uv sync`, `pip install -e .`, etc.). Solo hace falta **`POSTGRES_URI`** en `.env` (Alembic no carga JWT/R2/OpenAI al migrar):

```bash
python -m alembic upgrade head
```

Tras actualizar backend: nuevas tablas Field (p. ej. `field_instrument_revisions` PRE-FIELD) requieren esta migración en cada entorno.

## CI / contrato PRE-FIELD

GitHub Actions (`/.github/workflows/ci.yml`) ejecuta Pytest; el test `tests/test_instrument_spec_contract.py` valida el ejemplo oficial contra `examples/instrument_spec_v1.schema.json`. Localmente:

```bash
uv sync --extra dev
uv run pytest tests/ -q
```
