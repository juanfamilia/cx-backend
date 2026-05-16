# 7Field — PRE-FIELD INTELLIGENCE (especificación v1)

**Estado:** borrador ejecutable para producto e ingeniería. **Compacta** el “qué construir” de la capa previa al levantamiento; **no** duplica la visión del maestro salvo donde hace falta contrato explícito.

**Documentos base:**

- **Gobierno cerrado (ADR):** [adr/001-pre-field-brief-framework-ai-guide-bank-governance.md](adr/001-pre-field-brief-framework-ai-guide-bank-governance.md).
- **Modelo canónico PRE-FIELD** (entidades, snapshots, IA trace package, biblioteca, gates): [7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md](7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md).
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

**Idea fuerza:** 7Field **no “crea preguntas”** como decisión autónoma de método; crea **lógica metodológica**, **estructura**, **consistencia** y **control**. La IA **acelera y propone** (construcción, sugerencias, validación ampliada, síntesis, reutilización); **no** sustituye framework + humano — reglas, gates, waivers y aprobaciones siguen explícitos.

**Contrato único de observabilidad:** las salidas PRE-FIELD deben alinearse al **mismo modelo de hallazgos auditables** que Field, scoring, Readiness y capa ejecutiva (premisa 6 del maestro). **FrameworkWaiver** va ligado a **`instrument_revision_id`** (no herencia automática en revisión mayor); **orden de trabajo ingeniería:** **A→G** en ADR/modelo canónico — primero contrato, snapshots, lineage, gates servidor, trazabilidad IA y storage; **después** UX nueva y biblioteca.

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

---

## 6. Flujo operativo (usuario) — tres capas

El recorrido objetivo en producto **no** es solo “pasar al JSON”: debe reflejar **brief → técnico → inteligencia**, con humano en el centro.

### Capa 1 — Entrada y brief

- **Meta:** garantizar que equipo y sistema **entienden lo que el cliente desea** antes de estructurar el instrumento.
- **Contenido típico:** objetivos de negocio / investigación, audiencia, hipótesis, restricciones (tiempo, muestra, marca), entregables, tipo de estudio tentativo, documentos adjuntos si aplica.
- **Regla de producto:** no promover a “construcción de instrumento” hasta cumplir **criterios de brief suficiente** (plantillas configurables).
- **Estado en ingeniería:** captura guiada en UI + persistencia (`field_brief` o equivalente) — **backlog**; el objetivo conceptual queda fijado aquí.

### Capa 2 — Técnico, versionado y asignación

- **Meta:** gobierno del artefacto en el modelo canónico: **FieldStudy**, **FieldProject**, revisiones `instrument_spec`, Framework Library, validación schema, Auto QA, Readiness L4.
- **Estado:** **implementado** en backend y parcialmente en frontend (PRE-FIELD paso técnico + visualización de borradores).

### Capa 3 — Inteligencia asistida + banco de guías

- **Entradas obligatorias:** brief (capa 1) + **framework explícito** (plantillas/reglas versionadas — negociable pero siempre **acotado** para evitar “inventos” metodológicos de la IA).
- **Salidas:** sugerencias de **cuestionario** o **guía** según tipo de estudio y objetivos (estructura, bloques, ítems borrador, redacción sugerida); todo **etiquetado como sugerencia**, registrado y revisable por humano.
- **Principio:** la IA **complementa** criterio y creatividad humanos; **no** sustituye decisión metodológica ni publicación sin gates existentes.
- **Banco de guías:** tras **aprobación del cliente**, permitir **promover** la guía / kit aprobado a un **repositorio reutilizable** (tenant o catálogo global según política), con trazabilidad al brief y framework usados.
- **Estado:** contrato de datos y jobs IA — **backlog**; Framework Library y `instrument_spec` preparan el marco determinístico sobre el que debe operar la capa 3.

### Secuencia resumida (una línea)

**Brief completo → asignación y revisiones técnicas → sugerencias IA acotadas → revisión humana → QA / Readiness → (opcional) publicación al banco de guías tras aprobación cliente → export / handoff a EMS → campo.**

Errores y pérdidas en ejecución siguen en **Field Control** ya implementado; PRE-FIELD alimenta **calidad upstream** y reduce costo de error.

---

## 7. API REST (`/api/v1/field`)

**Implementado (persistencia + auditoría schema):** tabla `field_instrument_revisions`, multi-tenant por `company_id` + FK a `field_studies`, índice único parcial `(study_id, revision_label)` sobre filas activas, campos `last_validation_*` tras `POST .../validate`, **`brief_snapshot_hash`**, **`framework_catalog_version`**, **`last_ruleset_version`** (último tras QA). **Brief por estudio:** `field_study_brief` (`payload_json`, `body_hash`, `completeness_score`, `approval_state`, dual aprobación interno/cliente); **`field_studies.primary_language`**. **Waivers:** `field_framework_waivers` ligados a **`instrument_revision_id`**. **Auto QA bootstrap:** tabla `field_instrument_qa_runs`, motor determinístico **QA_RULE_001–005** (`QA_RULESET_BOOTSTRAP_V1`). **Readiness Gate L4:** `company_field_readiness_policy` incluye **`require_brief_approved`** (opcional; si `true`, código `brief_not_approved` hasta brief `approved_internal` o `approved`), `field_readiness_signatories`, `field_readiness_signatures` (snapshot `spec_hash` + `qa_run_id`); revisión pasa a **`approved`** cuando política + QA + schema + firmas requeridas están en verde. **Framework Library:** tabla `field_framework_templates`, seed versionado (`2026.1`), **`GET /field/framework-templates`** y borrador desde catálogo vía `framework_template_slug` en **`POST .../instrument-revisions`**.

| Método | Ruta | Propósito |
|--------|------|-----------|
| `POST` | `/field/instrument-spec/validate` | Validación JSON Schema **stateless** (`InstrumentSpecValidationReport`: `ok`, `schema_issues`, `content_hash`). |
| `GET` | `/field/framework-templates` | Catálogo de plantillas activas (`coverage_rules`, `stub_spec_json`); query opcional `study_type` (enum `instrument_spec`). |
| `GET` | `/field/studies/{study_id}/brief` | Brief del estudio (`FieldStudyBriefPublic`: `payload_json`, `body_hash`, `approval_state`, …). |
| `PATCH` | `/field/studies/{study_id}/brief` | Actualiza `payload` / `completeness_score` (bloqueado si brief ya en estado aprobado para gates). |
| `POST` | `/field/studies/{study_id}/brief/approve-internal` | Marca brief `approved_internal`. |
| `POST` | `/field/studies/{study_id}/brief/approve-client` | Marca `approved` (requiere `approved_internal` previo). |
| `GET` | `/field/studies/{study_id}/instrument-revisions` | Lista revisiones activas del estudio (sin `spec` completo; liviano). |
| `POST` | `/field/studies/{study_id}/instrument-revisions` | Crea `draft`; copia **`brief_snapshot_hash`** vigente; persiste **`framework_catalog_version`** cuando hay plantilla; ver body existente. |
| `GET` | `/field/instrument-revisions/{revision_id}` | Detalle + **`spec`** completo (`FieldInstrumentRevisionWithSpec`; incluye lineage en metadatos). |
| `PATCH` | `/field/instrument-revisions/{revision_id}` | Solo `draft`: reemplazo de `spec`, metadata; `status=archived` para cerrar (edición bloqueada después). |
| `GET` | `/field/instrument-revisions/{revision_id}/framework-waivers` | Lista waivers de framework de la revisión. |
| `POST` | `/field/instrument-revisions/{revision_id}/framework-waivers` | Registra waiver (`rationale`, `waived_sections`); solo revisión `draft`. |
| `POST` | `/field/instrument-revisions/{revision_id}/validate` | Ejecuta schema, persiste auditoría (`last_validation_at`, `last_validation_ok`, `issue_count`, `content_hash`) y devuelve informe. |
| `POST` | `/field/instrument-revisions/{revision_id}/qa-run` | Ejecuta QA_RULE_001–005 y guarda corrida; actualiza **`last_ruleset_version`** en la revisión. |
| `GET` | `/field/instrument-revisions/{revision_id}/qa-runs` | Historial de corridas QA (`limit` 1–100; últimas primero). |
| `GET` | `/field/instrument-revisions/{revision_id}/study-intelligence` | Motor **Study Intelligence**: journey participante, QA instantáneo (sin nueva corrida persistida), Readiness, insights — ver `7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md`. |
| `GET` | `/field/readiness-policy` | Política efectiva (`FieldReadinessPolicyPublic`; incluye **`require_brief_approved`**). |
| `PUT` | `/field/readiness-policy` | Upsert política (solo **superadmin** o **gerente** de la empresa). |
| `GET` | `/field/readiness-signatories` | Lista signatarios autorizados (cuando `enforce_signatory_grants=true`). |
| `POST` | `/field/readiness-signatories` | Alta signatario (mismo control que PUT política). |
| `DELETE` | `/field/readiness-signatories/{id}` | Baja lógica signatario. |
| `GET` | `/field/instrument-revisions/{revision_id}/readiness` | Estado agregado: `blocked` \| `pending_signatures` \| `ready` \| `approved`, códigos de bloqueo (`brief_not_approved` si política lo exige), firmas vigentes. |
| `POST` | `/field/instrument-revisions/{revision_id}/readiness-sign` | Firma nominal + snapshot; si queda **ready**, revisión → `approved`. |

**Parámetro recurrente:** `company_id` query para **rol 0** cuando aplique la misma regla que el resto de Field.

**Backlog (siguiente oleada):**

| Área | Propósito |
|------|-----------|
| Brief UX + plantillas por tipo de estudio | Reglas de completitud en UI; campos mínimos configurables |
| Capa IA acotada | Jobs/servicios con paquete trazabilidad ADR obligatorio + proyección a hallazgos |
| Banco de guías | Promoción post-aprobación a catálogo reutilizable (tenant/global) |
| Motor QA ampliado | Pesos por severidad, lexicones versionados, reglas MONITOR (fatiga, orden bloques), IA async informativa |
| Storage adjuntos brief | R2/S3 + metadata versionada (ADR) |
| Overrides L3 contractuales | Waivers de gate Readiness con ticket/motivo auditado (distinto del waiver de framework) |

**Seguridad:** `require_field_product_access`, staff Field (`assert_field_staff`), sin exposición PII en esta capa.

---

## 8. Frontend (Angular) — línea base

- Área **PRE-FIELD** bajo proyecto Field (`/field/project/:id/pre-field`): hoy cubre **sobre todo la capa 2** (objetivo/proyecto, plantillas, borradores, vista JSON).
- **Roadmap UX alineado a §6:** pasos o pestañas explícitos **Brief** · **Técnico / versiones** · **Sugerencias IA** · **QA** · **Readiness** · **Historial**; entrada desde selector de estudio / proyecto.
- **Banco de guías:** acción “promover a biblioteca” cuando la revisión esté **aprobada** y el cliente haya dado visto bueno al kit — backlog.

---

## 9. Orden comercial (recordatorio)

No vender PRE-FIELD aislado primero. Historia acordada: **Field Control → Auto QA → Backcheck → Cost of Error → Clever**. PRE-FIELD hospeda **Auto QA** como pilar transversal.

---

## 10. Backlog de ingeniería (checklist)

| # | Ítem | Notas |
|---|------|--------|
| 1 | Tablas persistencia PRE-FIELD | **`field_instrument_revisions`**, **`field_instrument_qa_runs`**, Readiness (`policy`, `signatories`, `signatures`). Tabla aparte `instrument_qa_findings` normalizada — backlog opcional |
| 2 | Motor QA_RULE_001–005 sobre JSON cargado | **Implementado** — `app/services/instrument_qa_rules_v1.py` + `POST .../qa-run` |
| 3 | Firmas Readiness L4 + políticas bloqueo | **Implementado** — tablas `company_field_readiness_policy`, `field_readiness_signatories`, `field_readiness_signatures`; evaluador `field_readiness_evaluator` |
| 4 | Seed `field_framework_templates` + catálogo API | **Implementado** — migración `z1y2x3w4v5u6`, `GET /field/framework-templates`, creación borrador con `framework_template_slug` |
| 5 | OpenAPI tags **Siete Field — PRE-FIELD** | Rutas documentadas en mismo tag `Siete Field` |
| 6 | Job IA / asistencia | Cola async cuando exista; **ningún run sin paquete ADR** (`framework_template_id`, `framework_version`, `rule_pack_version`, `model_version`, `prompt_version`, `brief_snapshot_hash`, actor, tenant, timestamp); proyección a **hallazgos** donde negocio lo defina |
| 7 | Enlace `FieldProject.study_id` población desde UI estudio | Ya soportado en PATCH proyecto |
| 8 | **Capa 1 — Brief** | **Backend:** `field_study_brief`, rutas GET/PATCH/aprobaciones, hash + gate Readiness opcional (`require_brief_approved`). **Pendiente:** plantillas por tipo, UX, adjuntos R2/S3 |
| 9 | **Capa 3 — IA + banco + waiver framework** | Waivers API (`field_framework_waivers`). **Pendiente:** jobs IA paquete ADR, biblioteca, publish global |

---

## Versionado del documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| **v1.9** | 2026-05-16 | §7 tabla API: `GET .../instrument-revisions/{id}/study-intelligence` (motor Study Intelligence). |
| **v1.8** | 2026-05-11 | §7: API brief, waivers por revisión, lineage revisión/QA, política `require_brief_approved`; backlog ajustado (adjuntos, IA, biblioteca). |
| **v1.7** | 2026-05-11 | §1 contrato único hallazgos; rol IA ampliado; waiver por revisión; orden A→G; §10 ítem 6 paquete trazabilidad IA obligatorio. |
| **v1.6** | 2026-05-11 | Encabezado: enlaces a **ADR 001** y **modelo canónico** como fuente normativa de gobierno y dominio. |
| **v1.5** | 2026-05-11 | **Flujo §6 en tres capas** (brief → técnico → inteligencia + banco de guías); principio IA complementaria y framework explícito; backlog §7 saneado; frontend §8 alineado a roadmap UX; checklist §10 ítems 8–9. |
| **v1.4** | 2026-05-10 | Framework Library: tabla `field_framework_templates`, `GET /field/framework-templates`, borrador desde plantilla (`framework_template_slug`). |
| **v1.3** | 2026-05-09 | Readiness Gate L4: política por empresa, signatarios, firmas con snapshot, estado agregado y transición `approved`. |
| **v1.2** | 2026-05-08 | QA_RULE_001–005 bootstrap: motor determinístico, tabla `field_instrument_qa_runs`, `POST/GET .../qa-run(s)`. |
| **v1.1** | 2026-05-08 | API implementada: revisiones persistidas, validate stateful/stateless, auditoría `last_validation_*`; migración `field_instrument_revisions`. |
| **v1.0** | 2026-05-06 | Primera especificación: módulos, dominio, API blueprint, límites, alineación L2–L5 y ejemplo/schema `instrument_spec`. |
