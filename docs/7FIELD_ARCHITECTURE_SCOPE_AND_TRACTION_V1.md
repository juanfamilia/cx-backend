# 7Field — Plan de arquitectura, alcance y tracción comercial (para iniciar código)

**Estado:** activo — documento operativo de **producto + ingeniería**.  
**Lectura recomendada antes de primer sprint de implementación.** Relacionado: [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md), [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md), [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md).

---

## 1. Resumen ejecutivo (una página)

| Dimensión | Qué fijamos aquí |
|-----------|------------------|
| **Arquitectura** | Capas **Pre‑Field**, **Field Execution Control**, **Post‑Field / inteligencia ejecutiva** dentro de **un solo producto 7Field**, un **shared contract** (hallazgos, severidad, criticidad operativa, decisiones auditables, versionado de reglas). |
| **Alcance código** | Por **fases incrementales** que mapean a los **tres pilares vendibles** sin construir “todo Layer 1” de golpe. |
| **Tracción comercial** | Cada fase tiene **historia vendible**, **demo posible** y **prueba de valor** antes de invertir en lo siguiente. |

**Principio:** Field sigue como **puerta comercial**; Pre‑Field y motor económico se **añaden** como inevitabilidad, no como ruido de features ([estrategia comercial](7FIELD_COMMERCIAL_STRATEGY_V1.md)).

---

## 2. Arquitectura objetivo (realista)

### 2.1 Mapa de capas lógicas

```
                    ┌─────────────────────────────────────┐
                    │      Pre‑Field Intelligence            │
                    │  (estudio, instrumento versionado,     │
                    │   Auto QA, readiness gate humano)     │
                    └──────────────┬──────────────────────┘
                                   │ artefactos + hallazgos
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│              Field Execution Control (ancla actual)           │
│  ingest CSV / conectores · reglas deterministas · scoring     │
│  hallazgos · riesgos · decisiones auditables · jobs async     │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│     Post‑Field: priorización · Cost of Error · exports          │
└──────────────┬───────────────────────────────────────────────┘
               │ solo datos gobernados
               ▼
┌──────────────────────────────────────────────────────────────┐
│   Clever — Executive Intelligence (opt‑in por tenant/plan)   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Responsabilidades por componente backend (orientación)

| Componente | Rol |
|------------|-----|
| **API REST (FastAPI)** | CRUD tenant‑scoped; hallazgos; proyectos Field; estudios/readiness cuando existan tablas; **nunca** lógica de negocio “secreta” solo en rutas sin servicio/versionado. |
| **Servicios de dominio** | Reglas deterministas; emisión de `finding`; vínculos `study_version` ↔ `field_project` (cuando exista); orquestación **sin** peso en request HTTP más allá del MVP. |
| **Workers / jobs async** | Re‑procesos, análisis batch, correlaciones tipo “priorizar backcheck”, QA pesado sobre archivos grandes. |
| **Rule / scoring governance** | `rule_versions` / `scoring_version_id`: **siempre** que el resultado sea comparable o contractualmente sensible ([gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)). |
| **Auditoría** | Decision logs, uploads, cambios de reglas, uso de Clever sobre datos sensibles (evolucionar hacia política enterprise). |

### 2.3 Multi‑tenant

- `company_id` (y donde aplique `end_client`/proyecto) en todas las filas nuevas de negocio.
- Overrides de reglas **solo** como entidades governadas con el mismo vigor que reglas globales.

### 2.4 Estado actual en código (línea base real)

Útil para que el equipo no reinvente:

- Field: proyectos, import CSV, capa decisión Dooblo/analysis, hallazgos, **approval + decision log** sobre hallazgos (trazabilidad de decisión).
- Contrato conceptual de hallazgos y severidad ya evolucionando según docs de **criticidad operativa** y **STOP / FIX_NOW / MONITOR** (implementación modelo de datos pendiente donde no exista campo).

Este documento parte de esa base y define **qué viene después**, no reescribe el monolito desde cero.

---

## 3. Alcance por fases (qué código, en qué orden)

Los **tres pilares comerciales** ([estrategia](7FIELD_COMMERCIAL_STRATEGY_V1.md)) se traducen en **fases** que pueden solaparse en ingeniería, pero **prioridad nominal** así:

---

### Fase A — Consolidar núcleo Field + contrato ejecutable (**ya en marcha → cerrar)**

**Objetivo comercial:** “control de campo defendible” + “decisiones con memoria auditada”.

**Alcance técnico típico:**

- Modelo de datos alineado a **criticidad operativa** + `operational_gate` donde aplique ([gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)).
- `scoring_version_id` / reglas efectivas donde **ya exista scoring** reproducible en disputas (mínimo: snapshot en resultado o en hallazgo).
- QA de API: permisos por tenant; explainability por hallazgo (regla, umbral **versionado** cuando exista registro).

**Fuera de alcance en A:** nuevo estudio/readiness grande, Clever ejecutivo nuevo.

**Tracción comercial:** casos donde el cliente necesita **parar campo** o documentar decisión ante auditoría → **primer renovación**.

---

### Fase B — **Auto QA de cuestionario** (Pre‑Field Intelligence — MVP ejecutable)

**Objetivo comercial:** “no quemamos presupuesto con instrumento defectuoso”.

**Alcance técnico típico (MVP brutal, no Suite Qualtrics):**

- Entidad **instrumento** o **revisión de instrumento** versionada: referencia a archivo (JSON/QSF export / PDF), hash, metadatos, responsable.
- Job async: **motor de reglas deterministas** sobre representación interna (parsing parcial admitido donde el equipo elija formato primero — p. ej. extracto de script o archivo intermedio) → emite hallazgos con `finding_code`, **STOP**/FIX_NOW/MONITOR según tabla de mapeo.
- UI mínima: lista de hallazgos de QA + sello/readiness (**roles 0 y 1** según política ya fijada en gobierno).
- Sin “deploy automático” a ninguna captura.

**Fuera:** anti‑bias mágico, ML detector de alma del cuestionario.

**Tracción comercial:** demo en **10 minutos**: subir archivo → lista de errores graves → CFO ve **cost avoided** en Fase D si están acoplados; si no, al menos STOP claro.

---

### Fase C — **Backcheck Intelligence**

**Objetivo comercial:** “revisamos lo que rompe negocio, no todas las filas”.

**Alcance técnico típico:**

- Sobre mismos **`field_import_rows` / caso / encuestador** que ya ingestan: función de scoring o rank (determinista v1 con pesos **versionados**).
- Lista priorizada (“top‑N sospechosos”) + explicabilidad (**por qué** sube score).
- Job async para recomputación al cerrar día/corrida.

**Fuera de C v1:** modelo ML opaco como única razón del rank.

**Tracción comercial:** “reducimos tiempo de equipo de campo en control efectivo”; métricas internas **tiempo a validar caso crítico**.

---

### Fase D — **Cost of Error Calculator**

**Objetivo comercial:** lenguaje CFO; conversión renewal.

**Alcance técnico típico:**

- Modelo configurado por tenant o por tipo de proyecto: **parámetros** (costo medio fallo recontacto, costo día campo, tasas…) **no** hardcode disperso.
- Cada hallazgo o proyecto puede tener **impacto económico estimado** + supuestos (texto reproducible para auditoría).

**Fuera:** forecasts financieros certificados por Big Four.

**Tracción comercial:** **una pantalla ejecutiva**: “orden de magnitud perdida si ignoramos estos 5 hallazgos esta semana”.

---

### Fase E — Clever Executive Intelligence (**después de** hallazgos + costos gobernados)

Entrada sólo **`findings` + scoring + contexto** según política ([gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)): storyline, priorización, export **board‑ready**.

**Sin** Clever antes de tener datos **consistentes**, queda “IA vacía” y destruye tracción.

---

## 4. Plan de trabajo sugerido (equipos pequeños)

Orden pragmático **para iniciar código ya**:

1. **Cerrar Fase A** en modelo + API donde falte (**contrato ejecutable**, no pantallas nuevas por vanidad).
2. **Paralelo ligero**: diseño de **Fase B MVP** — definir **un** formato de entrada del instrumento primero y reglas cerradas (~10–30 reglas ejecutables año 1).

**No abrir tres frentes** (auto QA pesado + backcheck + dinero sin Fase A).

---

## 5. Tracción comercial por fase (qué vendes y qué muestras)

| Fase | Mensaje único ante cliente | Prueba rápida (demo / piloto) |
|------|-----------------------------|--------------------------------|
| **A** | “Sabemos frenar donde hay riesgo y dejamos rastro defendible.” | Flujo proyecto → hallazgo bloqueante → decisión registrada exportable. |
| **B** | “Antes del campo sabemos si el instrumento nos va a hacer perder dinero.” | QA en archivo real del cliente → lista STOP/FIX_NOW. |
| **C** | “No revisamos todo — priorizamos el fraude/el error caro primero.” | Rank de IDs con texto explicable **por pesos/reglas**. |
| **D** | “Aquí están los pesos en dinero plausible.” | Misma lista con ** orden de magnitud** y supuestos. |
| **E** | “Menos tablas, historia ejecutiva desde lo ya probado.” | Generación texto/PDF desde bundle gobernado. |

Sin fila usable en esa tabla para una capacidad nueva → **no entra sprint** antes de historia clara ([estrategia](7FIELD_COMMERCIAL_STRATEGY_V1.md) §1).

---

## 6. Riesgos si se empieza “mal” código

| Riesgo | Mitigación mínima |
|--------|-------------------|
| Añadir tablas aisladas Pre‑Field sin **`field_project` / mismo contrato hallazgos** | Vínculos explícitos desde diseño físico modelo ERD. |
| Scoring cambia sin **`scoring_version_id`** histórico | Bloqueante para Fase D y enterprise. |
| Clever antes de datos | Desactivado por tenant o detrás flag; no POC demos con prompt suelto. |

---

## 7. Definition of Ready para el **primer sprint de nueva capacidad**

Antes de abrir IDE en Fase B+:

- [ ] Historia usuaria enlazada a **uno** de los tres pilares (Auto QA / Backcheck / Cost of Error).
- [ ] Lista de **5–15 reglas o señales** que la primera versión **sí o sí** debe detectar/ranquear/costear.
- [ ] **Formato del instrumento/dato**: qué entrada se admitirá en v1.
- [ ] Criterios de STOP/FIX/MONITOR documentados una vez sin ambigüedad.
- [ ] Quién puede **sellar** readiness (roles ya acordados: 0 / 1).

Sin eso → **spike exploratorio máximo 3 días**, no sprint blindado “de producto”.

---

## Versionado

- **v1 (2026‑02‑23):** plan arquitectura + fases + tracción alineadas a código y a [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md).

Referencias: [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md) · [FIELD_CSV_2026_1.md](FIELD_CSV_2026_1.md) según aplique ingest.
