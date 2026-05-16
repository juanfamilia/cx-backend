# 7Field — PRE-FIELD modelo canónico y bounded contexts (v1.3)

**Estado:** activo — **contrato de dominio** derivado del [ADR 001 — Brief, Framework, IA, Banco de guías](adr/001-pre-field-brief-framework-ai-guide-bank-governance.md). Objetivo: que backend, UX y auditoría compartan **la misma verdad** sin reabrir filosofía en cada sprint.

### Principio de plataforma (fuera solo de PRE-FIELD)

En **todo** 7Field, la dirección es que **observaciones relevantes converjan en hallazgos auditables bajo el mismo contrato** (fuente, severidad, vínculos a reglas/versiones, tenant, actor donde aplique) — PRE-FIELD, Field, scoring, IA, Readiness y capa ejecutiva. Evitar subsistemas que “cuenten cosas” sin camino de auditoría al mismo modelo de hallazgo.

**Audiencia:** arquitectura, backend, producto UX, seguridad.

**No sustituye:** detalle de rutas HTTP en [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md); amplía **entidades, ciclo de vida y gates**.

---

## 1. Bounded contexts

| Contexto | Responsabilidad | No hace |
|----------|-----------------|--------|
| **Study & Brief** | Brief persistente por estudio; completitud; aprobaciones interno/cliente; adjuntos versionados; idioma primario del estudio | No sustituye `instrument_spec` ni firma Readiness |
| **Instrument Revision** | Versionado de `instrument_spec`; vínculo a Study; snapshots/hash de brief; waivers de framework | No es fuente del brief (solo referencia) |
| **Framework & QA** | Plantillas versionadas; reglas determinísticas; corridas QA; readiness según L4 | No publica IA sin trazabilidad ni sin gates |
| **AI Assistance** | Borrador v0 y sugerencias **siempre** atadas a framework + waiver opcional; salida dual spec-diff + texto libre | No redefine método sin framework_id/version; no omite paquete de trazabilidad |
| **Guide Library** | Activos reutilizables (estructura/lógica/copy opcional); ámbito tenant vs global readonly; promoción auditada | No incluye mapping EMS en v1 |

---

## 2. Entidades lógicas (normativas)

### 2.1 `FieldStudy` (existente — extensiones requeridas)

| Campo / concepto | Regla |
|------------------|--------|
| `primary_language` | Idioma principal del estudio (código estable acordado por producto, p. ej. BCP-47). |
| `localized_variants` | Los instrumentos pueden tener variantes por locale; el dominio **no** asume monolingüe. |

### 2.2 `FieldBrief` (pertenece al Study)

- **FK:** `study_id` (única fuente de verdad del contenido de brief **actual** según política de edición).
- **Tipo de estudio:** determina el **set mínimo obligatorio** de campos (plantilla por `study_type` o equivalente).
- **`completeness_score`:** derivado o persistido; siempre visible para UX y Gates.
- **`approval_state`:** máquina de estados explícita en implementación; debe distinguir borrador / pendiente / aprobado interno / aprobado cliente cuando aplique.
- **`approved_by_internal`:** usuario interno que marca brief aprobado (nullable hasta aprobar).
- **`approved_by_client`:** usuario cliente final cuando modelo B2B2B (nullable hasta existir portal o proceso equivalente).
- **Timestamps** de aprobación por carril si negocio lo distingue (recomendado para auditoría).

**Regla:** Field Project **no** posee el brief; solo puede **consumir** estado derivado vía Study.

### 2.3 Snapshots de brief en revisión

Cada `InstrumentRevision` debe poder demostrar **qué brief regía** al crearse o al sellarse:

| Campo / concepto | Regla |
|------------------|--------|
| `brief_snapshot_hash` | Hash del snapshot canónico del brief (contenido serializado acordado). |
| `brief_snapshot_ref` | Opcional: puntero a fila/version de snapshot inmutable si se guarda histórico formal. |

**Regla de producto:** cambio **significativo** de brief ⇒ **nueva revisión mayor** del instrumento (definición operativa de “significativo”: tabla de triggers en implementación — debe ser auditable y documentada en migración).

### 2.4 `FieldBriefAttachment`

| Campo / concepto | Regla |
|------------------|--------|
| Storage | Object storage **S3-compatible** (p. ej. R2). |
| `storage_key` / URI interna | Referencia estable al objeto. |
| `content_hash` | Integridad y auditoría. |
| `version_id` | Versión lógica del adjunto (lineage). |
| `uploaded_by`, `uploaded_at` | Auditoría obligatoria. |
| Vínculo | Asociado al Study/Brief (no “metadata suelta” sin objeto). |

### 2.5 `FrameworkWaiver` (**cerrado:** ligado a revisión)

- **FK obligatoria:** `instrument_revision_id`. **Prohibido** anclar el waiver solo a `study_id` como fuente de verdad de la excepción.
- **Razón de dominio:** el waiver debe referir el **estado exacto del instrumento** (payload / revisión) que se cubre excepcionalmente.
- **Herencia:** ante **nueva revisión mayor** por cambio sustantivo de instrumento (o política explícita de “significativo”), el waiver **no** se propaga automáticamente — exige **reevaluación** humana y nuevo registro si aplica.
- Texto/rationale **obligatorio**; referencia al framework “base”; actor y timestamp; alcance (secciones/reglas declaradas no aplicables).

### 2.6 `AiAssistanceRun` (cada corrida registrable)

**Paquete obligatorio — ningún job sin estos campos persistidos (reproducibilidad + auditoría enterprise):**

| Campo | Descripción |
|-------|-------------|
| `framework_template_id` | Framework explícito. |
| `framework_version` | Versión **efectiva** del template en el momento de la corrida (línea reproducible junto al id). |
| `rule_pack_version` | Versión del paquete de reglas determinísticas aplicable al contexto. |
| `model_version` | Identificador reproducible del modelo de IA (convención interna; puede encapsular proveedor+modelo si se estandariza así). |
| `prompt_version` | Versión del prompt / paquete de redacción IA acordado por producto. |
| `brief_snapshot_hash` | Hash del brief vigente (o snapshot) al momento de la corrida. |
| `actor` | Usuario o identidad de servicio interna **acotada** que dispara la corrida. |
| `tenant` | Scope tenant resoluble (p. ej. `company_id` efectivo). |
| `generated_at` | Marca temporal (`timestamp`). |

**Salidas:**

1. **Diff estructurado** contra `instrument_spec` (o propuesta de revisión nueva), siempre etiquetado como sugerencia hasta aceptación humana.
2. **`free_text_artifacts`** para guías cualitativas — **no** sustituyen `instrument_spec` como fuente canónica del instrumento cuantitativo estructurado.

### 2.7 `GuideLibraryAsset`

| Campo / concepto | Regla |
|------------------|--------|
| Payload | Estructura, bloques, lógica; copy opcional según flags. |
| `reusable_structure_only` | Boolean semántico claro para usuarios y exports. |
| `reusable_copy_allowed` | Boolean — si false, instanciación copia estructura pero fuerza re-edición de copy según UX. |
| `scope` | `tenant_private` \| `global_catalog_readonly` (v1: global **solo lectura** para tenants; publicación workflow posterior). |
| `approved_for_library_by`, `approved_at` | Mínimo para ingreso al banco **sin** exigir Readiness L4 completo. |
| `owner` | Responsable (usuario y/o tenant según política). |

**Instanciación:** **siempre** crea **nueva** `InstrumentRevision`; prohibido sobrescribir borrador existente.

---

## 3. Matriz de gates (normativa UX + servidor)

| Acción | Gate típico |
|--------|----------------|
| Marcar **Brief Approved** | Completitud mínima por tipo **y** score según política **y** rol humano autorizado |
| Generar **borrador v0** con IA | Framework explícito + paquete de trazabilidad completo + brief en estado compatible (definir en implementación: al menos “no vacío” o umbral de score) |
| Transición **Readiness** / firma L4 | Entre otros: **`brief.approval_state == approved`** (según enumeración implementada) |
| Promover a **Guide Library** | `approved_for_library_by` + `approved_at` + owner; **no** requiere L4 completo |

Los gates deben repetirse **servidor-side** donde el riesgo sea bypass por API.

---

## 4. Prioridad de implementación (alineada ADR)

Orden normativo para ingeniería — **antes** de abrir nuevas superficies UX grandes:

| Paso | Enfoque |
|------|---------|
| A | Contrato y gobierno (enums, políticas, errores explícitos) |
| B | Snapshots, hashes, lineage de reglas y de aprobaciones |
| C | Gates server-side |
| D | Paquete de trazabilidad IA obligatorio en todo job |
| E | Guide Library (tenant + catálogo global readonly) |
| F | UX refinada |
| G | Integraciones avanzadas |

---

## 5. Explícitamente fuera de v1

- **Mapping/export EMS** (Qualtrics, Dooblo, etc.) como parte del banco de guías o del mismo paquete de promoción.
- **`publish_to_global`** desde tenant hacia catálogo editable global (post‑v1).

---

## 6. Alineación con decisiones estructurales existentes

- **L2:** `instrument_spec` sigue siendo formato canónico de instrumento estructurado.
- **L3:** **Study** sigue siendo ancla; Brief se modela **colgando del Study**, no del Field Project.
- **L4:** Readiness permanece firma humana y políticas; este documento **añade** dependencia normativa de brief aprobado donde aplique.

---

## 7. Extensión — Study Intelligence (motor backend)

La plataforma incorpora **inteligencia de estudio** como capacidad de servidor: recorrido del participante (`participant_journey` / `journey_phase`), señales metodológicas, fatiga, riesgos operacionales, zonas de abandono esperado, scoring contextual, insights con prioridad y continuidad serializable **PRE‑FIELD → FIELD**. Norma de implementación y capas L1–L9: **[7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md](7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md)**. Contratos runtime: `app/study_intelligence/contracts.py`; orquestación: `StudyIntelligenceService`; **prompts LLM** solo vía `app/study_intelligence/prompt_registry.py` (sin strings dispersos en servicios).

Persistencia de tablas dedicadas es **roadmap** (fases P1–P4 del blueprint); el modelo canónico v1 sigue anclado en Study, Brief, `instrument_revision`, QA runs y Readiness. **P2 en curso:** snapshots `field_participant_journeys` / `field_journey_phases` al calcular Study Intelligence (ver blueprint §7).

---

## Versionado del documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| **v1.3** | 2026-05-16 | §7 nota P2: tablas `field_participant_journeys` / `field_journey_phases` (snapshots Study Intelligence). |
| **v1.2** | 2026-05-16 | §7 extensión Study Intelligence — enlace blueprint backend, contratos Python, política prompt registry; línea base vs persistencia P2+. |
| **v1.1** | 2026-05-11 | Principio plataforma hallazgos únicos; **FrameworkWaiver** cerrado a `instrument_revision_id`; paquete IA alineado ADR (`model_version`, `actor`, `tenant`, `timestamp`); §4 orden implementación A–G (§5 exclusiones v1). |
| **v1.0** | 2026-05-11 | Primera versión: bounded contexts, entidades, gates, exclusiones v1, alineación L2–L4. |
