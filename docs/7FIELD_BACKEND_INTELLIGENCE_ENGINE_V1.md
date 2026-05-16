# 7Field — Motor backend de inteligencia de estudio (blueprint v1)

**Estado:** activo — **contrato de arquitectura** para backend. Objetivo: que **toda** inteligencia metodológica, journey, fatiga, scoring contextual e insights **nazcan en el servidor**, versionada y auditable; el frontend **solo humaniza** la salida (ver § contrato en [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md)).

**Audiencia:** backend, ML/IA aplicada, producto técnico, Cursor/agents.

**No sustituye:** modelo PRE-FIELD canónico ni ADR 001 — **extiende** el dominio hacia journey intelligence operativo y continuidad PRE-FIELD → FIELD.

---

## 1. Principios obligatorios

1. **Backend = motor.** Framework catalog + rule packs + heurísticas CX + análisis de journey + fatiga + scoring contextual + generación de insights + interpretación operativa + continuidad hacia Field + exportadores + mappings EMS.
2. **Sin prompts dispersos.** Todo texto LLM vive en un **registro central versionado** (`app/study_intelligence/prompt_registry.py` y artefactos asociados en repo); los servicios **referencian** `prompt_id` + versión, no strings inline ad hoc.
3. **Patrones metodológicos reales.** Calibrar reglas y plantillas con práctica reconocible (Ipsos, Kantar, NielsenIQ, Gallup, Bain CX, Qualtrics XM Institute, Forrester, ESOMAR, MRS, estándares UX research, JTBD, CX maturity, etc.) — **traducidos** a reglas audtables y UX humano, no teoría en API.
4. **Percepción deseada:** mezcla creíble de **consultor senior + director metodológico + operaciones inteligentes**.
5. **Continuidad PRE-FIELD → FIELD.** El mismo bundle de contexto (journey, riesgos, prioridades, señales) debe poder **serializarse y reusarse** en overview/decisión Field cuando exista vínculo estudio–proyecto.

### 1.1 Readiness oficial vs QA dinámico (semántica única)

| Concepto | Qué es | UI / API |
|----------|--------|----------|
| **Readiness + validaciones persistidas** | Estado **oficial**, auditado: política empresa, firmas, última validación de **esquema** (`last_validation_*`), corrida QA **persistida** (`field_instrument_qa_runs`) donde aplique. | Etiquetas tipo «última validación guardada», panel Readiness, gates L4. |
| **QA / study-intelligence en vivo** | Pasada **consultiva** sobre el `instrument_spec` y brief **actuales** (`GET .../study-intelligence`): QA_RULE bootstrap instantáneo + heurísticas journey sin sustituir el ledger oficial. | Etiquetas tipo «Recomendación actual» / motor dinámico; **no** mezclar copy ni semáforos con el estado Readiness sin aclarar. |

**Regla:** nunca presentar ambos como la misma fuente de verdad. Si en el futuro se unifica lectura operativa, debe ser decisión explícita de producto + migración de contrato.

---

## 2. Capas de servicio (paquete Python)

| Capa | Nombre orientativo | Responsabilidad |
|------|-------------------|-----------------|
| **L1** | **Framework rules engine** | Plantillas `FrameworkTemplate`, versiones de catálogo, cobertura metodológica declarada vs `instrument_spec` + brief. |
| **L2** | **QA heuristics** | Auto QA determinístico (existente `instrument_qa_runtime`) + expansiones; severity y vínculos a bloques/ítems. |
| **L3** | **Journey analysis** | Construcción de `participant_journey` / `journey_phase` desde `instrument_spec` + brief + tipo de estudio. |
| **L4** | **Operational interpretation** | Riesgos operacionales, zonas de abandono esperado, áreas de sensibilidad — enlazados a fases/bloques. |
| **L5** | **Fatigue & bias signals** | Señales de fatiga, sesgo, redundancia, orden, consistencia, longitud (salidas tipadas). |
| **L6** | **Contextual scoring** | Scores por dimensión (ej. riesgo de campo, calidad de medición, alineación brief) con **versionado de fórmula**. |
| **L7** | **Insight generation** | Ensambla **insights automáticos** human-readable + prioridad + trazabilidad a regla/heurística. |
| **L8** | **Recommendation engine** | Siguiente mejor acción sugerida (sin ejecutar gates por sí mismo — respeta Readiness L4). |
| **L9** | **Study intelligence facade** | Orquesta L1–L8 para una revisión/estudio; punto único para APIs futuros (`StudyIntelligenceService`). |

**Integraciones existentes:** hoy `field_instrument_qa_services.py` + `instrument_qa_rules_v1.py` cubren parte de **L2**. El roadmap mueve **L3–L8** bajo `app/study_intelligence/` sin romper contratos vigentes.

---

## 3. Entidades lógicas (persistencia — roadmap)

Nombres en **snake_case** alineados a tablas futuras. Claves foráneas típicas: `study_id`, `instrument_revision_id`, `company_id`, `field_project_id` (opcional, cuando exista continuidad Field).

### 3.1 `participant_journey`

| Concepto | Regla |
|----------|--------|
| Ancla | Una fila por **versión analizada** (p. ej. por `instrument_revision_id` + `analysis_run_id` o snapshot hash). |
| Payload | Fases ordenadas, metadatos de fuente (`instrument_spec` hash, `brief_snapshot_hash`, framework_version). |
| Objetivo | Fuente canónica para UI “Recorrido del participante” y para Field. |

### 3.2 `journey_phase`

| Concepto | Regla |
|----------|--------|
| FK | `participant_journey_id`. |
| Campos | `phase_key` estable (intro, screening, core_experience, …), `order_index`, títulos humanos, refs a `block_id[]`. |
| Narrativa | Texto derivado por motor (no hardcoded en frontend). |

### 3.3 `operational_risk`

| Concepto | Regla |
|----------|--------|
| Uso | Riesgo operacional contextual (despliegue, muestra, cuotas, captura EMS). |
| Trazabilidad | `source_rule_id` o `heuristic_id`; severidad alineada con hallazgos donde aplique. |

### 3.4 `methodological_signal`

| Concepto | Regla |
|----------|--------|
| Uso | Señal metodológica (cobertura, gap vs framework, orden subóptimo). |
| Severidad | Compatible con STOP / FIX_NOW / MONITOR o escala paralela documentada. |

### 3.5 `fatigue_risk`

| Concepto | Regla |
|----------|--------|
| Uso | Estimación de carga/fatiga por tramo o instrumento completo. |
| Entrada | Longitud, tipo de ítem, matrices, repeticiones. |

### 3.6 `sensitivity_area`

| Concepto | Regla |
|----------|--------|
| Uso | Bloques/temas sensibles (finanzas, salud, laboral) inferidos de brief + texto ítems. |

### 3.7 `expected_dropout_zone`

| Concepto | Regla |
|----------|--------|
| Uso | Fases o ítems donde el modelo predice mayor abandono (heurística + datos históricos cuando existan). |

### 3.8 `insight_priority`

| Concepto | Regla |
|----------|--------|
| Tipo | Enum normativo (p. ej. `must_act`, `high`, `medium`, `low`, `fyi`) para ordenar UI y alertas. |

**Contratos runtime** (previos a migraciones): `app/study_intelligence/contracts.py`.

---

## 4. Versionado inteligente

- Cada corrida de análisis debe registrar: **ruleset_version**, **framework_catalog_version**, **journey_engine_version**, **scoring_formula_version**, **prompt_bundle_version** (si IA).
- **Lineage:** mismos principios que `brief_snapshot_hash` / `content_hash` en revisiones — recomputar o invalidar análisis ante cambio sustantivo.

---

## 5. Exportadores y mappings EMS

- **Exportadores:** JSON canónico del bundle de inteligencia + formatos acordados por cliente (post‑MVP).
- **Mappings EMS:** tabla/config versionada por proveedor (Qualtrics, Dooblo, …) que traduce bloques/ítems canónicos ↔ artefactos externos; **no** en el frontend.

---

## 6. IA / LLM

- Solo dentro de **insight generation** o **recommendation engine**, con **prompt_registry** y trazabilidad alineada a `AiAssistanceRun` del modelo canónico (framework_id, rule_pack_version, prompt_version, brief_snapshot_hash).
- Preferir **extractos pequeños** + **clasificación** sobre generación larga sin control.

---

## 7. Fases de implementación sugeridas

| Fase | Entrega |
|------|---------|
| **P0** | Contratos Python + `prompt_registry` + facade (`StudyIntelligenceService`). |
| **P1** | **`GET /field/instrument-revisions/{revision_id}/study-intelligence`** — `StudyIntelligenceBundlePublic` (journey + QA instantáneo `QA_RULESET_BOOTSTRAP_V1` + Readiness + insights); implementación `app/study_intelligence/pipeline.py`. |
| **P2** | Tablas **`field_participant_journeys`** + **`field_journey_phases`**; upsert en cada `GET .../study-intelligence` (mismo `revision_id` + `instrument_spec_content_hash`); respuesta incluye `participant_journey_snapshot_id`. Persistencia ampliada (insights JSON, runs QA) — backlog. |
| **P3** | Señales fatiga/sesgo/redundancia ampliadas + scoring contextual versionado. |
| **P4** | Propagación a Field overview / findings priority cuando exista estudio vinculado. |

---

## Versionado del documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| **v1.3** | 2026‑05‑16 | P2 parcial: tablas `field_participant_journeys`, `field_journey_phases`; upsert al responder `study-intelligence`; `participant_journey_snapshot_id` en JSON. |
| **v1.2** | 2026‑05‑16 | §1.1 semántica Readiness oficial vs QA/study-intelligence dinámico (sin mezclar en UI). |
| **v1.1** | 2026‑05‑16 | P1: endpoint `study-intelligence`, pipeline + `journey_heuristics` + esquemas Pydantic; P1 marcado entregado en §7. |
| **v1.0** | 2026‑05‑16 | Blueprint motor backend: capas, entidades, prompts centralizados, continuidad Field, export/mappings, fases P0–P4. |
