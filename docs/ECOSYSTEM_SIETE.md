# Ecosistema Siete (tenant / sub-tenant / productos)

**Visión:** Siete Inteligencia Creativa **no** es una colección de pantallas aisladas ni “productos” solo por menú: es un **ecosistema de inteligencia aplicada** y **memoria metodológica viva** — Field, CX, InS, Clever y Perfil comparten **contexto, identidad, lenguaje, señales y continuidad**. Dirección transversal: [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md).

**Criterios de plataforma, ancla comercial (Field) y contrato mínimo compartido (hallazgos, auditoría, decisiones):** [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md)

**Hallazgos, tri‑estado operativo (STOP / FIX_NOW / MONITOR), versionado de scoring y Clever:** [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)

**Estrategia comercial y prioridades (top 3 vendibles):** [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md)

**Plan de arquitectura, alcance y tracción para iniciar código:** [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md)

**Decisiones estructurales cerradas (motor reglas, formato Auto QA, Study canónico, Readiness, límites Clever):** [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md)

## Tenant y sub-tenant

- **Tenant** = `companies` (firma de investigación o cliente Siete).
- **Sub-tenant** = `end_clients` (cliente final del estudio). Un cliente puede tener **varios** proyectos Field; cada proyecto pertenece a **un** cliente.

## Productos (flags en `companies`)

| Columna | Producto |
|---------|----------|
| *(implícito)* | **CX** — siempre `true` en `GET /entitlements/me` para un tenant válido. |
| `siete_ins_enabled` | **InS** — investigación cualitativa (sesiones, pipeline evolutivo). |
| `siete_field_enabled` | **Field** — PRE-FIELD (diseño del estudio) + FIELD (supervisión operativa); sin sustituir EMS de captura. |
| `siete_clever_enabled` | **Clever** — aceleración ejecutiva; no sustituye reglas ni hallazgos oficiales. |
| *(roadmap / modelo evolutivo)* | **Perfil** — identidad y contexto del usuario o equipo en el ecosistema (preferencias, continuidad entre productos); activación técnica según evolución de `companies` / perfil extendido. |

Activación InS/Field/Clever: superadmin vía `PUT /company/{id}` (`CompanyUpdate`). **Perfil** se documenta aquí como pilar de producto; el mecanismo exacto de flag o tabla seguirá el contrato de plataforma cuando se formalice en código.

## API transversal

- `GET /api/v1/entitlements/me?company_id=` — flags de productos para el usuario actual (rol 0 puede consultar otro tenant).

## End clients

- `GET /api/v1/end-clients?company_id=` — lista (roles 0, 1, 2).
- `POST /api/v1/end-clients` — crea (`EndClientCreate`: `name`, opcionales `external_ref`, `notes`, `company_id` para rol 0).

## Field (MVP)

- `GET /api/v1/field/access` — probe (sin requerir flag).
- `GET/POST /api/v1/field/projects` — requiere `siete_field_enabled` (salvo rol 0 siempre puede llamar; la creación sigue necesitando tenant válido).

Ver formato CSV piloto: [FIELD_CSV_2026_1.md](FIELD_CSV_2026_1.md).

## Migración

Revisión Alembic: `l6m7n8o9p0q1` (tras `k5l6m7n8o9p0`).
