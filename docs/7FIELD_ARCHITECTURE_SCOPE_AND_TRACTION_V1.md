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

## 2. Flujo natural

### 2.1 Ciclo del estudio (orden temporal en el mundo real)

Así opera una firma cuando el producto está **completo** (referencia conceptual, no “todo existe en v1 del código”):

1. **Define** el problema de negocio y el diseño (brief, muestra declarada, instrumento).
2. **Valida** el instrumento **antes de despachar campo** → aquí encaja **Auto QA** + **sellado humano** (readiness): evitar capex perdido por instrumento contaminado.
3. **Ejecuta** el levantamiento → **Field**: ingest CSV/conectores, reglas deterministas sobre filas/eventos, **hallazgos** y **scores** reproducibles (**versión de reglas**).
4. **Controla** sin revisar todo: **priorización** de casos (backchecks, sospechas, fraude material) donde el volumen lo exija.
5. **Decide** con trazabilidad: estados **STOP / FIX_NOW / MONITOR**, **decision logs**, ownership.
6. **Cuantifica** pérdida o riesgo en **orden de magnitud económico** cuando el método lo permite → **Cost of Error**.
7. **Sintetiza** para dirección **solo** sobre datos ya gobernados → **Clever** (Executive Intelligence), no sobre ruido bruto.

En una frase (alineada con plataforma): **señal → riesgo → decisión → acción → aprendizaje**; el “aprendizaje” alimenta reglas/versiones posteriores, no parámetro oculto.

### 2.2 Flujo natural de implementación (lo que viene primero en código)

El **orden comercial top 3** (Auto QA · Backcheck · Cost of Error) no es siempre idéntico al **primer merge** cuando ya hay producto Field en uso:

| Orden en la vida real (§2.1) | Qué paralelizar primero en ingeniería (este documento) |
|------------------------------|---------------------------------------------------------|
| Pre‑field Auto QA antes de ejecutar campo | Primero **Fase A**: núcleo Field + contrato ejecutable (**criticidad operativa**, `operational_gate`, versionado donde ya hay scoring) — porque es **fundación única de hallazgos y auditoría**. |
| Control en ejecución + priorización de revisión | Luego **Fase C** (Backcheck Intelligence) cuando el núcleo y finding pipeline son **estables**. |
| Hablar CFO | **Fase D** cuando hallazgos y supuestos de costo pueden **referenciar** reglas/versiones sin retrabajar. |

**Auto QA (Fase B)** entra cuando la **fundación Hallazgos + Tenant + Decisiones** está cerrada suficientemente; si no, el pre‑campo emitiría señales **sin mismo contrato que Field** → se rompe narrativa enterprise.

Clever (**Fase E**) es **naturalmente al final**: consume lo que los pasos previos ya **sellaron**.

**Regla práctica:** el flujo natural de usuario es **PRE → FIELD → POST → ejecutivo**. El flujo natural **de arranque de código actual** sigue siendo **A → B → C → D → E** en las secciones siguientes — detallado en §4 (alcance por fases) y §5 (plan de trabajo).

---

## 3. Arquitectura objetivo (realista)

### 3.1 Mapa de capas lógicas

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

### 3.2 Layer 2 — Field Execution Control (**core; no negociable**)

Todo lo siguiente define el **mínimo conceptual y de producto** de la capa Field Execution Control. No se interpreta como roadmap opcional: las fases (§4) ordenan **cuándo** se cierra cada pieza en código, no si existe.

| Área | Qué debe cubrir Layer 2 |
|------|-------------------------|
| **Cuotas y control operativo** | Control de cuota (coherencia, desvíos, políticas acordadas). |
| **Calidad de respuesta / fraude de superficie** | Duración anormal; straight lining; patrones repetitivos; señales de falsificación potencial (determinista y explicable en v1). |
| **Geolocalización** | GPS inconsistente o incompatible con reglas de campo (según datos disponibles por conector). |
| **Riesgo agregado** | Scoring de riesgo reproducible; **riesgo por encuestador**, **por supervisor**, **por zona**, **por proyecto** (roll‑ups auditables). |
| **Acción y gobierno** | Alertas **accionables** (no solo métricas); **trazabilidad** de regla/versión/supuesto donde aplique; **auditoría** humana y de sistema alineada a decision logs y hallazgos. |

**Principio:** Pre‑Field (Layer 1+) y Post‑Field / Clever **no sustituyen** este núcleo: lo consumen o lo priorizan. Features que no enlazan hallazgos, scoring versionado cuando sea contractual, y auditoría **no cuentan** como Layer 2 completo.

### 3.3 Responsabilidades por componente backend (orientación)

| Componente | Rol |
|------------|-----|
| **API REST (FastAPI)** | CRUD tenant‑scoped; hallazgos; proyectos Field; estudios/readiness cuando existan tablas; **nunca** lógica de negocio “secreta” solo en rutas sin servicio/versionado. |
| **Servicios de dominio** | Reglas deterministas; emisión de `finding`; vínculos `study_version` ↔ `field_project` (cuando exista); orquestación **sin** peso en request HTTP más allá del MVP. |
| **Workers / jobs async** | Re‑procesos, análisis batch, correlaciones tipo “priorizar backcheck”, QA pesado sobre archivos grandes. |
| **Rule / scoring governance** | `rule_versions` / `scoring_version_id`: **siempre** que el resultado sea comparable o contractualmente sensible ([gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)). |
| **Auditoría** | Decision logs, uploads, cambios de reglas, uso de Clever sobre datos sensibles (evolucionar hacia política enterprise). |

### 3.4 Multi‑tenant

- `company_id` (y donde aplique `end_client`/proyecto) en todas las filas nuevas de negocio.
- Overrides de reglas **solo** como entidades governadas con el mismo vigor que reglas globales.

### 3.5 Estado actual en código (línea base real)

Útil para que el equipo no reinvente:

- Field: proyectos, import CSV, capa decisión Dooblo/analysis, hallazgos, **approval + decision log** sobre hallazgos (trazabilidad de decisión).
- Contrato conceptual de hallazgos y severidad ya evolucionando según docs de **criticidad operativa** y **STOP / FIX_NOW / MONITOR** (implementación modelo de datos pendiente donde no exista campo).

Este documento parte de esa base y define **qué viene después**, no reescribe el monolito desde cero.

---

## 4. Alcance por fases (qué código, en qué orden)

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

## 5. Plan de trabajo sugerido (equipos pequeños)

Orden pragmático **para iniciar código ya**:

1. **Cerrar Fase A** en modelo + API donde falte (**contrato ejecutable**, no pantallas nuevas por vanidad).
2. **Paralelo ligero**: diseño de **Fase B MVP** — definir **un** formato de entrada del instrumento primero y reglas cerradas (~10–30 reglas ejecutables año 1).

**No abrir tres frentes** (auto QA pesado + backcheck + dinero sin Fase A).

---

## 6. Tracción comercial por fase (qué vendes y qué muestras)

| Fase | Mensaje único ante cliente | Prueba rápida (demo / piloto) |
|------|-----------------------------|--------------------------------|
| **A** | “Sabemos frenar donde hay riesgo y dejamos rastro defendible.” | Flujo proyecto → hallazgo bloqueante → decisión registrada exportable. |
| **B** | “Antes del campo sabemos si el instrumento nos va a hacer perder dinero.” | QA en archivo real del cliente → lista STOP/FIX_NOW. |
| **C** | “No revisamos todo — priorizamos el fraude/el error caro primero.” | Rank de IDs con texto explicable **por pesos/reglas**. |
| **D** | “Aquí están los pesos en dinero plausible.” | Misma lista con **orden de magnitud** y supuestos. |
| **E** | “Menos tablas, historia ejecutiva desde lo ya probado.” | Generación texto/PDF desde bundle gobernado. |

Sin fila usable en esa tabla para una capacidad nueva → **no entra sprint** antes de historia clara ([estrategia](7FIELD_COMMERCIAL_STRATEGY_V1.md) §1).

---

## 7. Riesgos si se empieza “mal” código

| Riesgo | Mitigación mínima |
|--------|-------------------|
| Añadir tablas aisladas Pre‑Field sin **`field_project` / mismo contrato hallazgos** | Vínculos explícitos desde diseño físico modelo ERD. |
| Scoring cambia sin **`scoring_version_id`** histórico | Bloqueante para Fase D y enterprise. |
| Clever antes de datos | Desactivado por tenant o detrás flag; no POC demos con prompt suelto. |

---

## 8. Definition of Ready para el **primer sprint de nueva capacidad**

Antes de abrir IDE en Fase B+:

- [ ] Historia usuaria enlazada a **uno** de los tres pilares (Auto QA / Backcheck / Cost of Error).
- [ ] Lista de **5–15 reglas o señales** que la primera versión **sí o sí** debe detectar/ranquear/costear.
- [ ] **Formato del instrumento/dato**: qué entrada se admitirá en v1.
- [ ] Criterios de STOP/FIX/MONITOR documentados una vez sin ambigüedad.
- [ ] Quién puede **sellar** readiness (roles ya acordados: 0 / 1).

Sin eso → **spike exploratorio máximo 3 días**, no sprint blindado “de producto”.

---

## 9. Objetivos primero — honestidad sobre el repositorio actual

**Regla:** el éxito se mide por **cumplimiento de objetivos de negocio y contrato**, no por proteger el código existente. Si el diseño actual **impide** gobierno de reglas, comparabilidad histórica o Pre‑Field al mismo estándar que Field, **hay que revisar y cambiar** (esquema, servicios o límites del monolito) con decisión explícita; no “parchear forever”.

### 9.1 Lo que el código actual sí soporta (línea base real, no marketing)

- Proyectos Field, import CSV, corridas, hallazgos en `field_findings`, políticas versionadas por proyecto (`field_policy_sets`) en JSON.
- Capa decisión Dooblo/async con motor de reglas **acotado** (p. ej. cuotas) en código Python (`app/integrations/field_decision_engine.py`; códigos canónicos Layer 2 en `app/integrations/field_finding_codes.py`), extensible pero **no** aún un **Rule Configuration Engine** gobernado como activo.
- **Auditoría de decisiones humanas** sobre aprobación de hallazgos (`field_finding_decision_logs`) + API/UI recientes.
- Multi‑tenant básico vía `company_id` en entidades Field.

Esto **no es menor**: es una base para **Field Execution Control** y trazabilidad parcial.

### 9.2 Brechas frente a los objetivos documentados (las que obligan revisión seria)

| Objetivo (docs) | Estado típico en repo | Implicación |
|-----------------|------------------------|-------------|
| **Criticidad operativa** + **STOP / FIX_NOW / MONITOR** distintos de `severity` UI | Hallazgo tiene `severity` (info/warn/error), **sin** campos explícitos de criticidad ni gate operativo en BD | Requiere **evolución de modelo** + migración + mapping desde reglas; **no** bastan etiquetas solo en frontend. |
| **Reglas de scoring como activos versionados** (`scoring_version_id`, rollback, audit de cambios) | Política en JSON por política/proyecto; **sin** tabla única de versiones de reglas/scoring con vigencia y aprobaciones como en [gobierno](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md) | Riesgo de **parámetros opacos** y comparabilidad débil; **decisión de producto**: modelo nuevo o evolución fuerte de `field_policy_sets` + tabla de governance. |
| **Auto QA pre‑campo** integrado al mismo contrato de hallazgos | No hay flujo de **instrumento versionado** ni job de QA como ciudadano de primer clase enlazado a `study`↔`field_project` unificado | Pre‑Field **no puede ser solo carpeta de código**: hace falta **dominio + migraciones** (o integración explícita con otro módulo si se elige no monolito). |
| **Estudio unificado** (programa / diseño) vs Field project | Existen otros estudios en otros productos (p. ej. rutas InS); **no** está garantizado un **vínculo canónico** estudio‑Field como única fuente de verdad | Si la narrativa comercial exige “este levantamiento opera bajo diseño X”, hay que **diseñar el vínculo** y evitar duplicar entidades incompatibles. |
| **Cost of Error Calculator** | Sin modelo de parámetros económicos por tenant ni campos de estimación en hallazgos | Implementación nueva; depende de hallazgos gobernados para no ser fantasía. |
| **Clever** sin caja negra | Sin barreras técnicas en código hasta donde alcance este repo — depende de política de datos + logging de uso | Producto + ingeniería deben imponer **contratos de entrada** antes de exponer a clientes regulados. |

**Conclusión:** el repo **permite seguir construyendo Field** y endurecer contratos **incrementalmente**, pero **no** cumple ya, por sí solo, el documento de **gobierno pleno** ni Pre‑Field Auto QA **sin** trabajo de modelo de datos y refactor organizado. Ignorar esta brecha para “ship rápido” genera deuda que **destruye venta enterprise**.

### 9.3 Cuándo aceptar refactor vs capa encima

| Señal | Tendencia recomendada |
|-------|------------------------|
| Cada nuevo hallazgo requiere **`if` hardcodeado** y no admitís versionado | Refactor hacia **motor + versiones persistidas**. |
| Equipo discute “¿qué política aplicó?” sin respuesta en BD | Parar features; implementar **trazabilidad de versión efectiva** en resultados. |
| Pre‑Field se implementa como microservicio separado sin contrato compartido | **Integración explícita** (API interna + mismos IDs tenant/hallazgo) o decisión de **bounded context** documentada — no acoplamiento solo por conveniencia. |

### 9.4 Acción recomendada antes de escalar inversión en código

1. **Sesión de arquitectura** (medio día): revisar este § frente a backlog real; listar **decisiones de modelo** bloqueantes.
2. **ADR cortos** (Architecture Decision Records): formato instrumento v1; tabla `rule_versions` vs extender políticas; vínculo estudio‑Field.
3. **No comprometer** fechas comerciales en Auto QA / governance **sin** cerrar ADRs anteriores.

**Decisiones estructurales cerradas** (motor de reglas, formato Auto QA, Study canónico, Readiness, Clever enforced): [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md).

---

## Versionado

- **v1 (2026‑02‑23):** plan arquitectura + fases + tracción alineadas a código y a [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md).
- **v1.1:** sección §2 **Flujo natural** — ciclo vivo del estudio vs orden de implementación (A→E).
- **v1.2:** §9 **Objetivos primero** — honestidad repo vs documentos de gobierno y Pre‑Field.
- **v1.3:** §3.2 **Layer 2 Field Execution Control** — alcance core no negociable (cuota, calidad respuesta, GPS, riesgo agregado, alertas, trazabilidad, auditoría).
- **v1.4:** §9.1 referencia a `field_finding_codes.py`; contrato de códigos Layer 2 en código.

Referencias: [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md) · [FIELD_CSV_2026_1.md](FIELD_CSV_2026_1.md) según aplique ingest.
