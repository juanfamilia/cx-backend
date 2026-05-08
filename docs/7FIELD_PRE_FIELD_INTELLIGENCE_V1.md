# 7Field — PRE-FIELD INTELLIGENCE (especificación v1)

**Estado:** borrador ejecutable para producto e ingeniería. **Compacta** el “qué construir” de la capa previa al levantamiento; **no** duplica la visión del maestro salvo donde hace falta contrato explícito.

**Documentos base:**

- Visión y UX: [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md) (sección PRE-FIELD).
- Decisiones cerradas (motor de reglas, formato QA, Study, Readiness, Clever): [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md).

---

## 1. Objetivo de producto

Ayudar a **construir, validar y auditar** el instrumento (cuestionario, screener, guía cualitativa, mystery shopper, backcheck) **antes** del campo, con:

- **Reglas metodológicas determinísticas** (Framework Engine + catálogo de QA versionado).
- **Buenas prácticas** embebidas en plantillas y checks.
- **IA asistiva** (borradores, redacción, detección ampliada) **sin** autoridad metodológica ni publicación sola.
- **Versionado y trazabilidad** por revisión de instrumento y por versión de reglas.
- **Readiness humano** obligatorio para estado “listo para campo” en producto.

**Idea fuerza:** 7Field **no “crea preguntas”** como decisión autónoma de método; crea **lógica metodológica**, **estructura**, **consistencia** y **control**. La IA **acelera y propone**; **no** sustituye framework + humano.

---

## 2. Límites (no negociables)

| Fuera de alcance PRE-FIELD como sustituto | Dentro de alcance |
|-------------------------------------------|-------------------|
| Reemplazar Qualtrics / Dooblo / EMS de captura | Artefacto canónico interno + export / copia guiada hacia EMS donde negocio lo permita |
| Scripting infinito estilo “ Survey IDE ” completa | Builder **estructurado** por secciones, tipos de ítem y plantillas |
| IA que decide diseño muestral o método sin trazabilidad | Recomendaciones **atingentes** a framework elegido + log de sugerencias |
| Publicación automática “live” sin gate | **Readiness Gate** con firmas humanas según L4 |

---

## 3. Cadena canónica de dominio (L3)

Alineado a **FieldStudy** (`field_studies`) y **FieldProject** con `study_id` opcional hoy; dirección de modelo:

```
FieldStudy (tenant-scoped)
  └── InstrumentRevision (versionado; payload instrument_spec + metadata)
       └── opcional: vínculo export / external_survey_ref (no duplica captura)
  FieldProject.study_id → FieldStudy
       └── Findings / scoring (post campo; ya existente en plataforma)
```

**InstrumentRevision** (conceptual hasta migración): cada fila es una **revisión inmutable** una vez “sellada” para auditoría; ediciones posteriores crean **nueva** revisión (`major.minor` o entero según política). Campos mínimos sugeridos:

- `study_id`, `revision_label` (ej. `v1.2`), `instrument_spec_version`, `spec_json` (o blob en storage + hash).
- `framework_template_id` + `study_goal_tags` (negocio).
- `status`: `draft` | `qa_pending` | `qa_failed` | `readiness_pending` | `approved` | `superseded`.
- `content_hash`, `created_at`, `created_by_user_id`.
- Tras aprobación: `approved_by_user_id`, `approved_at`, `rule_bundle_version` / `qa_ruleset_ref` aplicado en último run bloqueante.

---

## 4. Formato canónico del artefacto: `instrument_spec` (L2)

- **Único formato oficial de entrada para Auto QA v1:** JSON **`instrument_spec`** con `instrument_spec_version`, validado **servidor** contra esquema.
- Ejemplo en repo: [`examples/instrument_spec_v1.example.json`](../examples/instrument_spec_v1.example.json).
- Esquema draft: [`examples/instrument_spec_v1.schema.json`](../examples/instrument_spec_v1.schema.json).

**Tipos de ítem previstos (evolutivo):** single, multi, matrix, open, ranking, likert/numeric scale, quotas (donde el JSON declare strata), más metadatos de sección (intro, consentimiento, screener, bloque, demográficos, cierre).

**Ramificación:** grafo declarado (edges con `from` / `to` / condiciones); reglas determinísticas validan integridad (**QA_RULE_005**).

---

## 5. Módulos PRE-FIELD

### 5.1 Instrument Builder

**Función:** montaje guiado del `instrument_spec` por **secciones** y **tipos**, arrancando desde **tipo de estudio** y **objetivo de negocio**.

**Tipos de estudio iniciales (marketing / UX):** CX, U&A, Brand Tracking, Concept Test, Mystery Shopper, Focus Group.

**Salida:** borrador `instrument_spec` válido por schema + metadatos de plantilla aplicada.

### 5.2 Framework Library / Framework Engine

**Función:** **no** es una lista suelta de preguntas; es **patrones metodológicos** verificables (slots obligatorios/recomendados, orden sugerido, checks cruzados).

**Ejemplo CX (patrones verificables):** presencia estructural de hilos tales como experiencia reciente, touchpoint, satisfacción, fricción, recomendación — como **requerimientos de bloque o cobertura**, no como texto libre único.

**Implementación:** catálogo versionado `framework_templates` (id, versión, `study_type`, reglas de cobertura en forma machine-readable, copy UX humano).

### 5.3 Auto QA

**Función:** ejecutar **reglas determinísticas** sobre `instrument_spec` + (opcional) capa IA para **informativos** y sugerencias de redacción, siempre **etiquetadas** y **no bloqueantes** salvo política explícita.

**Severidades de producto:** `STOP` · `FIX_NOW` · `MONITOR`.

**Bootstrap obligatorio (L — anexo):** QA_RULE_001 … QA_RULE_005 en [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md).

**Contrato de hallazgo QA:** `source=instrument_qa_runtime`, referencias a `rule_id`, `instrument_revision_id`, `rule_version`; mismo espíritu que hallazgos de campo para trazabilidad.

### 5.4 Readiness Gate (L4)

Secuencia obligatoria en producto:

1. Sin **STOP** pendientes según política tenant/proyecto (configurable mínimo: al menos un bloqueante crítico detiene flujo).
2. Firmas humanas registradas: roles **Research**, **QA**, y **Account** si contrato lo exige — ver tabla L4 en decisiones estructurales.
3. Transición a estado **`approved` / ready for field** solo tras condiciones anteriores.

La IA **no** puede saltar este gate.

### 5.5 Versionado

- Cada revisión de instrumento y cada ejecución de QA relevante queda **auditada** (`approved_by`, `approved_at`, `rule_version`).
- Cambios sustantivos ⇒ **nueva** revisión, no sobrescribir la aprobada.

### 5.6 AI Assistance

**Permitido:** parafraseo, claridad, detección heurística ampliada, resumen de issues para el revisor, sugerencias de reorganización.

**Prohibido como comportamiento por defecto:** decisión sola de metodología, publicación sin Readiness, inyección de contenido sin trazabilidad en log de sugerencias.

### 5.7 Clever (relación)

Clever **no** autor el instrumento desde cero. Encaja **después**, sobre artefactos gobernados (resumen, narrativa, mejoras de storytelling). Ver L5 y doc de hallazgos.

---

## 6. Flujo operativo (usuario)

**Brief → scripting guiado → revisión manual → Auto QA → corrección → Readiness → (export / handoff a EMS) → campo.**

Errores y pérdidas en ejecución siguen en **Field Control** ya implementado; PRE-FIELD alimenta **calidad upstream** y reduce costo de error.

---

## 7. API REST (`/api/v1/field`)

**Implementado (persistencia + auditoría schema):** tabla `field_instrument_revisions`, multi-tenant por `company_id` + FK a `field_studies`, índice único parcial `(study_id, revision_label)` sobre filas activas, campos `last_validation_*` tras `POST .../validate`.

| Método | Ruta | Propósito |
|--------|------|-----------|
| `POST` | `/field/instrument-spec/validate` | Validación JSON Schema **stateless** (`InstrumentSpecValidationReport`: `ok`, `schema_issues`, `content_hash`). |
| `GET` | `/field/studies/{study_id}/instrument-revisions` | Lista revisiones activas del estudio (sin `spec` completo; liviano). |
| `POST` | `/field/studies/{study_id}/instrument-revisions` | Crea `draft`; `spec` opcional o plantilla mínima válida; `revision_label` opcional (`vN`). |
| `GET` | `/field/instrument-revisions/{revision_id}` | Detalle + **`spec`** completo (`FieldInstrumentRevisionWithSpec`). |
| `PATCH` | `/field/instrument-revisions/{revision_id}` | Solo `draft`: reemplazo de `spec`, metadata; `status=archived` para cerrar (edición bloqueada después). |
| `POST` | `/field/instrument-revisions/{revision_id}/validate` | Ejecuta schema, persiste auditoría (`last_validation_at`, `last_validation_ok`, `issue_count`, `content_hash`) y devuelve informe. |

**Parámetro recurrente:** `company_id` query para **rol 0** cuando aplique la misma regla que el resto de Field.

**Backlog (siguiente oleada):**

| Método | Ruta | Propósito |
|--------|------|-----------|
| `GET` | `/field/framework-templates` | Catálogo plantillas por `study_type`. |
| `POST` | `/field/instrument-revisions/{id}/qa-run` | Motor QA_RULE_* determinístico + hallazgos tipados. |
| `GET` | `/field/instrument-revisions/{id}/qa-findings` | Paginación hallazgos QA. |
| `POST` | `/field/instrument-revisions/{id}/readiness-sign` | Firma L4. |
| `GET` | `/field/instrument-revisions/{id}/readiness` | Estado readiness agregado. |

**Seguridad:** `require_field_product_access`, staff Field (`assert_field_staff`), sin exposición PII en esta capa.

---

## 8. Frontend (Angular) — línea base

- Nueva área bajo shell Field: p. ej. ruta **`/field/study/:studyId/pre-field`** o entrada desde selector de estudio (lista **FieldStudy** ya expuesta vía `/field/studies`).
- Tabs sugeridos: **Builder** · **QA** · **Readiness** · **Historial / versiones**.
- No implementado en este entregable documental; depende de priorización tras Field Control estable.

---

## 9. Orden comercial (recordatorio)

No vender PRE-FIELD aislado primero. Historia acordada: **Field Control → Auto QA → Backcheck → Cost of Error → Clever**. PRE-FIELD hospeda **Auto QA** como pilar transversal.

---

## 10. Backlog de ingeniería (checklist)

| # | Ítem | Notas |
|---|------|--------|
| 1 | Tablas `instrument_revisions`, `instrument_qa_findings`, `readiness_signatures` | **`field_instrument_revisions`** implementada; QA findings + readiness pendientes |
| 2 | Motor QA_RULE_001–005 sobre JSON cargado | Tests unitarios con `instrument_spec_v1.example.json` |
| 3 | Servicio `validate_instrument_spec` | JSON Schema en CI + **`POST .../validate`** y **`POST .../instrument-spec/validate`** |
| 4 | Seed de `framework_templates` mínimo (CX + uno cuanti genérico) | |
| 5 | OpenAPI tags **Siete Field — PRE-FIELD** | Rutas documentadas en mismo tag `Siete Field` |
| 6 | Job opcional IA | Cola async, mismo contrato de hallazgo |
| 7 | Enlace `FieldProject.study_id` población desde UI estudio | Ya soportado en PATCH proyecto |

---

## Versionado del documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| **v1.1** | 2026-05-08 | API implementada: revisiones persistidas, validate stateful/stateless, auditoría `last_validation_*`; migración `field_instrument_revisions`. |
| **v1.0** | 2026-05-06 | Primera especificación: módulos, dominio, API blueprint, límites, alineación L2–L5 y ejemplo/schema `instrument_spec`. |
