# ADR 001 — PRE-FIELD: Brief, Framework obligatorio, IA trazable y Banco de guías

**Estado:** Aceptado  
**Fecha:** 2026-05-11  
**Ámbito:** 7Field — PRE-FIELD (instrumentación antes del levantamiento)

---

## Contexto

PRE-FIELD mezcla **experiencia de usuario**, **gobierno**, **auditoría enterprise** y **asistencia IA**. Sin criterios cerrados, arquitectura y UX divergen (dónde vive el brief, qué puede hacer la IA, qué entra al banco de guías, qué bloquea Readiness).

Este ADR **cierra** política de producto y gobierno; el modelo físico detallado vive en [7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md](../7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md).

### Producto ancla

**7Field** sigue siendo el producto ancla: **no** es una plataforma de captura. Es una **capa de control operacional** — QA, readiness, riesgo y **gobierno** sobre estudios y ejecución de campo — interpretando ejecución desde datos que el cliente ya tiene en EMS/conectores.

### Principio rector (transversal a todo 7Field)

**Todo debe producir hallazgos auditables bajo el mismo contrato** — incluye PRE-FIELD, Field operativo, scoring, IA, Readiness y capa ejecutiva (Clever / intelligence). **No** subsistemas aislados sin proyección al mismo modelo de hallazgo, severidad y trazabilidad que el resto de la plataforma acuerde.

La prioridad comercial de espinazo sigue siendo: **Auto QA → Backcheck Intelligence → Cost of Error → Clever** como narrativa ejecutiva **gobernada**. Lo demás **refuerza** ese espinazo.

### Prioridad técnica inmediata (antes de UX nueva)

**No** abrir nuevas capacidades visuales como primer frente. Primero consolidar **contrato y gobierno en servidor**: snapshots y hashes, lineage de reglas, lineage de aprobaciones, metadata de object storage, **paquete de trazabilidad IA**, **gates server-side**. Eso es lo que hace el sistema **enterprise defendible**.

### Orden real de ejecución (obligatorio para roadmap)

| Orden | Frente |
|-------|--------|
| **A** | Contrato y gobierno |
| **B** | Snapshots y trazabilidad |
| **C** | Gates server-side |
| **D** | AI traceability |
| **E** | Biblioteca (Guide Library) |
| **F** | UX refinada |
| **G** | Integraciones avanzadas |

No invertir el orden (no “dashboard bonito” antes de infraestructura auditable).

---

## Decisión

### 1. Brief (capa 1)

- **“Brief suficiente” no es libre total:** conjunto mínimo obligatorio **por tipo de estudio**, más **brief completeness score**, más **aprobación humana explícita** (`Brief Approved`). La IA **no** sustituye estos tres elementos.
- **Titularidad:** el brief pertenece al **Study** canónico (`FieldStudy`), **no** al Field Project operativo ni a una revisión aislada como fuente de verdad.
- **Revisiones de instrumento:** cada revisión persiste **snapshot y/o hash** del brief vigente en el momento relevante; **cambio significativo de brief ⇒ bump de revisión mayor** (política de “significativo” se define en modelo canónico; debe ser auditable).
- **Aprobación dual (modelo desde v1):** soportar tenant interno **y** B2B2B end client mediante `approval_state`, `approved_by_internal`, `approved_by_client` (portal cliente puede llegar después; el **modelo** ya lo contempla).
- **Adjuntos:** almacenamiento **versionado** en object storage (R2/S3 compatible), metadata en BD, **hash**, `version_id`, `uploaded_by`, `uploaded_at`, auditabilidad enterprise.

### 2. Framework + IA (capa 3)

**PRE-FIELD oficial en tres frentes de producto:** **Brief** · **Técnico / instrumento versionado** · **Inteligencia + Banco de guías**.

- **La IA no sustituye el framework.** Acelera **construcción**, **sugerencias**, **validación ampliada**, **síntesis** y **reutilización**. Siguen gobernados explícitamente: **reglas**, **gates**, **waivers**, **aprobaciones** y **trazabilidad**.
- **Framework explícito siempre:** toda asistencia IA opera con **`framework_template_id`** y **`framework_version`** efectiva registradas (versión del template en el momento de la corrida); **nunca** IA totalmente libre.
- **Override (`FrameworkWaiver`):** **cerrado — ligado solo a `instrument_revision_id`**, **no** a `study_id`.  
  **Razón:** el waiver debe ser trazable al **estado exacto del instrumento** que se aprobó excepcionalmente. Si el instrumento cambia de forma **significativa** y origina **nueva revisión mayor**, el waiver **no** se hereda automáticamente — debe **reevaluarse** explícitamente.
- **Salidas IA:** (a) **diff estructurado** sobre `instrument_spec`; (b) **texto libre** para guías cualitativas. El **instrumento canónico** sigue siendo el JSON `instrument_spec` estructurado y versionado; el texto libre **no** lo reemplaza.
- **Trazabilidad obligatoria (bloqueante governance):** **ningún job de IA** ejecuta ni persiste resultado válido sin registrar **en la misma corrida**:  
  `framework_template_id`, **`framework_version`** (efectiva del template), `rule_pack_version`, **`model_version`** (identificador reproducible del modelo), `prompt_version`, `brief_snapshot_hash`, **`actor`** (`user_id` o identidad servicio interna acotada), **`tenant`** (`company_id` / scope tenant resoluble), **`timestamp`** (`generated_at`).  
  **Sin este paquete no hay gobierno válido** — todo debe ser reproducible y auditable en auditoría enterprise.

### 3. Banco de guías

- **Promoción:** puede incluir **estructura, bloques, lógica** y **copy literal opcional**; cada asset declara explícitamente **`reusable_structure_only`** y **`reusable_copy_allowed`**.
- **Ámbito v1:** activos **tenant-scoped**; más **catálogo global solo lectura** administrado por Siete. Workflow **`publish_to_global`** explícitamente **posterior**.
- **Reuso:** instanciar desde banco **siempre** crea **nueva** revisión de instrumento; **nunca** sobrescribe borrador ni revisión existente (lineage y trazabilidad).
- **Entrada al banco:** **no** exige Readiness L4 completo; sí exige **aprobación humana**, **owner**, **audit trail** mínimo: `approved_for_library_by`, `approved_at`.

### 4. Orden UX y gates

- **IA antes de revisión:** permitido **solo** para **borrador v0**; después siguen revisión técnica, QA y Readiness (la IA acelera arranque, no sustituye control).
- **Tabs paralelos / progreso visible:** sí, pero **gates obligatorios** y **re-evaluados en servidor** (ejemplo normativo: **no Readiness si brief ≠ approved**).
- **Tono UX:** operacional, claro, **auditado**, ejecutivo — **no** “AI playground”. El usuario debe poder afirmar: *sé qué está pasando y por qué* (estado, bloqueos, lineage visible donde aplique).

### 5. Integraciones e i18n

- **v1:** banco y governance **no** incluyen mapping EMS (Qualtrics/Dooblo); son artefacto metodológico interno; deployment técnico **desacoplado** y **posterior**.
- **Multi-idioma:** `Study.primary_language`; instrumentos con **variantes localizadas** como parte del dominio (LATAM regional).

---

## Consecuencias

- Ingeniería debe modelar **Brief**, **snapshots por revisión**, **attachments versionados**, **corrida IA con paquete de trazabilidad obligatorio**, **`FrameworkWaiver` con FK a `instrument_revision_id` únicamente** (sin herencia automática al bump mayor), **activos de biblioteca con flags de reuso** y **gates** en servicios (no solo en UX).
- Cambiar cualquier punto material de este ADR requiere **nuevo ADR** o revisión formal explícita; evitar reinterpretación en tickets sueltos.

---

## Referencias

- Modelo canónico y bounded contexts: [7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md](../7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md)
- Especificación PRE-FIELD (API, módulos): [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](../7FIELD_PRE_FIELD_INTELLIGENCE_V1.md)
- Decisiones estructurales L2–L4: [7FIELD_STRUCTURAL_DECISIONS_V1.md](../7FIELD_STRUCTURAL_DECISIONS_V1.md)
- Visión producto: [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](../7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md)
