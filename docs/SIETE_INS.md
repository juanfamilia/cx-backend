# Siete InS (investigación cualitativa)

Producto **separado** de Siete CX sobre la **misma infraestructura** (auth, empresa, pago, workers futuros, Stream/R2/Whisper cuando se cablee el pipeline).

## Estado actual (MVP)

- **Flag por empresa** `companies.siete_ins_enabled`: solo **rol 0** lo activa vía `PUT /api/v1/company/{id}` con cuerpo `CompanyUpdate` (`siete_ins_enabled: true`).
- **Tabla** `ins_studies`: estudios con título, objetivo, `status`, `pipeline_status`, `rubric_version` (anclaje futuro a guías versionadas).
- **API** bajo el mismo prefijo que CX: `/api/v1/ins/...`.
- **Pipeline** `POST /ins/studies/{id}/run`: por ahora marca `pipeline_status=ready` (stub). La secuencia real será: cola → vídeo/audio → transcripción → rúbrica → informe JSON + narrativa.

## Acceso

| Quién | Comportamiento |
|--------|----------------|
| Rol 0 | Siempre puede usar rutas InS (tras auth + pago). Listar estudios requiere `?company_id=`. Crear estudio puede usar `company_id` en el body aunque el flag InS esté apagado (arranque / demo). |
| Roles 1–3 | Requieren `siete_ins_enabled` en su empresa (`require_ins_product_access`). Sin flag: **403** en rutas protegidas. |
| `GET /ins/access` | Solo auth + pago: devuelve `{ ins_enabled, scope }` para que el front muestre u oculte el producto **sin** recibir 403. |

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ins/access` | Probe de licencia InS. |
| GET | `/ins/studies?company_id=` | Lista estudios (rol 0: `company_id` obligatorio). |
| POST | `/ins/studies` | Crea estudio (`InsStudyCreate`: `title`, `optional objective`, `company_id` solo rol 0). |
| GET | `/ins/studies/{id}` | Detalle. |
| POST | `/ins/studies/{id}/run` | Stub de pipeline (roles 0, 1, 2). |

## Código relevante

- Modelo: `app/models/ins_study_model.py`
- Empresa: `app/models/company_model.py` (`siete_ins_enabled`)
- Servicios: `app/services/ins_study_services.py`
- Dependencia de acceso: `app/utils/ins_access.py`
- Router: `app/routes/ins_router.py` (registrado en `app/routes/main.py`)
- Migración: `app/migrations/versions/k5l6m7n8o9p0_siete_ins_mvp.py`

## Próximos pasos (producto)

1. **Sesiones de vídeo** ligadas a un estudio (misma tubería que evaluaciones CX).
2. **Rúbrica versionada** (JSON esquema) + plantillas de informe.
3. **Jobs** con estados `queued → transcribing → analyzing → ready | failed` y trazabilidad.
4. **Matriz de capabilities** por rol (0–3) distinta a CX si hace falta.
5. **Front** Siete InS (app o rutas `/ins`) consumiendo `GET /ins/access`.

## Migración

Solo necesitas **`POSTGRES_URI`** en el entorno o en `.env` / `../.env` (Alembic ya no carga el resto de `Settings`).

Tras desplegar el backend, desde la raíz del repo (con dependencias instaladas en el entorno activo):

```bash
# Siempre funciona si Alembic está instalado en ese Python (Codespaces / venv / Docker):
python -m alembic upgrade head
```

Alternativas:

```bash
uv run alembic upgrade head
# o, con el venv activado (.venv/bin en PATH):
alembic upgrade head
```

(Revisión `k5l6m7n8o9p0` sobre `j4k5l6m7n8o9`.)
