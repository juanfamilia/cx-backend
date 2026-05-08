# 7Field — Decisiones estructurales cerradas (v1)

**Propósito:** sustituir **zonas grises** por línea base ejecutable para ingeniería. **No sustituye** la visión en [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md); **acota** cómo implantarla.

**Audiencia:** arquitectura, backend, seguridad producto — **sin** expansión funcional nueva en este documento.

**Estado:** **decisiones cerradas para implementación**; cambiar cualquier punto **obliga** nuevo ADR o revisión formal de esta versión.

---

## L1 — Motor de configuración gobernado (no solo JSON suelto)

**Decisión:** **no extendemos indefinidamente `field_policy_sets` como único soporte de gobierno enterprise.**

Se implanta —como trabajo de infraestructura de producto— un **Rule Configuration Engine** persistente que incluye, como mínimo conceptual:

| Requisito | Significado implementable |
|-----------|---------------------------|
| `rule_versions` | Registro inmutable o append-only por versión lógica; valor efectivo fecha **desde** / **hasta**. |
| `scoring_versions` (o análogo) | Agrupaciones de pesos/umbrales que **firmen** puntajes y clasificaciones exportables ([gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)). |
| Aprobaciones | Estados de ciclo previo a **efectiva** (quién puede aprobar rollout de versión nueva). |
| Rollback | Volver a **`rule_version`** vigente conocida sin editar historia. |
| Audit trail | Antes/después, actor, tenant scope, ticket/motivo. |
| Vigencia efectiva | Toda lectura aplicable debe resolver **qué paquete** rige ese `timestamp`/`field_project`. |

Las políticas actuales en JSON pueden **integrarse como payload** inicial o migrarse; lo que **ya no vale** como única solución es “parámetro en JSON sin trazabilidad de versión igual que el documento de plataforma exige”. Ver honestidad técnica en §9 de [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md).

---

## L2 — Auto QA v1 — **un solo** formato de entrada oficial

**Decisión:** el **único** formato oficial de entrada en **Auto QA v1** es **`instrument_spec`**: **JSON intermediario controlado**, esquema versionado (`instrument_spec_version`), validado servidor contra schema.

**Excluido del MVP oficial:** entrada primaria solo-PDF como **contrato estándar** (mayor tiempo de equipo, menor control). PDF u otros pueden ser **conversiones opcionales** posteriores, no formato canónico v1.

**Implicaciones:** export SurveyToGo (u otros) debe **traducirse** a este JSON en pipeline ingest (script, micro-conversión o proceso operativo hasta que exista herramienta automatizada por prioridad).

---

## L3 — Objeto canónico **Study** (única fuente de verdad)

**Decisión:** existe una entidad **`Study`** canónica (tenant-scoped `company_id`, identificadores estables).

**Cadena lineal conceptual obligatoria:**

```
Study
  └── Instrument Revision (instrumento/adjuntos versionados, hash)
       └── Field Project (ejecución)
            └── Findings (+ rule/scoring refs)
                 └── Executive / Clever (solo consumiendo lo anterior)
```

**Regla fuerte:** no se duplican “definiciones de estudio” coherentes dispersas entre módulos como fuentes paralelas irreconcilables: **Study** enlaza artefactos; **Field Project** lleva FK `study_id` (transición permite null solo con plan de migración explícito y fecha sunset).

InS u otros módulos pueden **referenciar** el mismo `study_id` cuando negocio lo permita; **no** se crean definiciones paralelas del mismo estudio sin vínculo explícito en modelo.

---

## L4 — Autoridad de Readiness

**Decisión:** el paso Readiness es **firma nominal** tecnológico: registra `signature_role_type` + **`signer_user_id`** + **`signed_at`** + snapshot link (hash de instrument/policy).

**Authority roles cerrados inicialmente:**

| Figura nominal | Obligación de producto |
|----------------|------------------------|
| **Research Lead** — metodología y validez de medición (`READINESS_ROLE_RESEARCH`) | Bloqueante para salida a campo salvo override contractual documentado por **gobernanza L3** donde aplique. |
| **QA Lead** — calidad técnica del instrument (`READINESS_ROLE_QA`) | Requerido en tier enterprise default. |
| **Account Director / sponsor comercial cliente** cuando contrato así lo establezca (`READINESS_ROLE_ACCOUNT`) | Obligatoriedad **por configuración cliente** tenant/proyecto, no opcional vagamente. |

Mapeos numéricos a roles RBAC concretos (0/1/nuevos flags) los define **tabla mapping** en siguiente iteración ingeniería; **no existe** “el equipo aprueba” sin usuarios registrados firmantes.

Sin conjunto aplicable configurado ⇒ **bloqueado** transición ejecutable a **Field live** donde producto así lo aplique (`readiness_blocked` estado explícito).

---

## L5 — Clever — límites **obligatorios**, no texto en manual

Además política (`CLEVER` entitlements):

| Límite | Enforcement implementable tipo |
|--------|-------------------------------|
| No PII innecesaria | Payload Clever sólo vistas **projection** servidor; filtros campo a campo; denies default. |
| No credenciales | Capa Clever nunca llamada rutas secreto vault; rutas públicas sólo después strip. |
| No cross tenant | Middleware inyectado `tenant_id` server-side irrevocable cliente petición usuario. |
| Hallazgos bloqueantes sin estado permitido para síntesis | Servidor rechaza si existe hallazgo **STOP** / criticidad bloqueante sin **resolución** según política (`eligible_for_executive_layer=false`). |
| Scoring sin versión efectiva | Rechazar payload Clever si falta `scoring_version_id` resoluble para KPI derivados. |
| Decisiones irreversibles desde texto modelo | Clever solo produce texto/resumen; **ningún side-effect** (bloqueo operativo, envío a cliente final, borrado) desde rutas Clever sin servicio humano/acuerdo explícito. |

**Ownership:** estos checks **no** son sólo UX — responsables Security + Backend + Producto Clever antes de GA enterprise.

---

## Anexo — Auto QA bootstrap: **reglas tangibles primera entrega**

Hasta tener este catálogo **implementable**, Auto QA permanece iniciativa no terminada conceptual — **implementación v1 debe cubrir** al menos estos **cinco** chequeos determinísticos cuando material exista en **`instrument_spec`**.

| Id | Área detectable | Ejemplo comportamiento inicial |
|----|-----------------|--------------------------------|
| **QA_RULE_001** | Doble pregunta (double‑barrel) localizado en mismo item textual donde semánticas separadas | marca **FIX_NOW** hasta separación física contenido. |
| **QA_RULE_002** | Leading / priming lexical high‑risk pattern list bilingual controlled | marca **STOP** sólo combinación severidad método acordado. |
| **QA_RULE_003** | Cuotas o targets muestra **imposibilidad algebraica**/suma≠100% strata definidos donde JSON declara proporciones cerradas ⇒ **STOP** |
| **QA_RULE_004** | Escalas inconsistentes entre cardinalidad declarada y etiquetas en el mismo bloque | **FIX_NOW** por defecto (severidad afinable por política). |
| **QA_RULE_005** | Grafos branching JSON inválido (destino inexistente, ciclo duro banned, unreachable critical items) ⇒ **STOP** |

**Posterior backlog no bloqueante v1 inicial:** fatiga tiempo estimativa (monitorea), mejoras orden bloques (**MONITOR**).

Todos los QA hallazgos comparten mismo **tipo contrato técnico** `source=instrument_qa_runtime` hasta split futuro granular.

---

## Próximo paso

| Acción siguientes 2‑4 semanas | Dueño típico |
|------------------------------|---------------|
| ADR físico ubicación nuevas tablas motor reglas naming | Backend lead |
| JSON schema `instrument_spec` draft + ejemplo en `examples/` (**hecho:** `instrument_spec_v1.schema.json`, `instrument_spec_v1.example.json`) — evolucionar con Builder | Backend + método |
| Modelo físico **InstrumentRevision** + QA findings + readiness signatures (ver [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md)) | Backend |
| Modelo físico inicial `study` + migra backfill provisional `field_projects` | Backend |
| Matriz Roles→Readiness permisos efectivos | Prod + seguridad |

**Este archivo es el fin de nueva narrativa hasta cerrar desarrollo motor reglas nivel 0.**

---

Referencias: [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md) · [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md) · [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)
