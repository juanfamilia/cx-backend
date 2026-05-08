# 7Field — Arquitectura de experiencia (producto)

**Estado:** activo — **documento maestro simple**: describe *qué debe sentir el usuario* y *qué construimos*. El detalle técnico, fases largas y gobierno profundo siguen en los enlaces al final.

---

## Premisas

1. **7Field no replica** Dooblo, Qualtrics ni ninguna herramienta de captura. **Interpreta ejecución** a partir de datos que el cliente ya tiene en esos sistemas (u otros conectores).
2. **Regla de 3 clics:** desde que el usuario entra con intención de ver campo, hasta tener **una lectura clara de “salud”** del negocio de campo, el flujo feliz no debe forzar más de **tres interacciones principales** (p. ej. login/config → lista/estatus → campaña/proyecto elegido). Todo lo demás es **profundización opcional**, no barrera.
3. **“Salud”** aquí significa: **KPIs acordados** + **scores / riesgo** derivados de reglas versionadas y, cuando aplique, **hallazgos** que explican *por qué* algo está en rojo o ámbar — no una tabla infinita de respuestas crudas.
4. **Misma lectura operativa para cualquier proveedor:** Dooblo, Qualtrics u otro sistema de levantamiento solo cambian la **tubería de ingesta**; quien use 7Field debe **entender lo mismo** — qué pasa en campo, salud del proyecto, alertas — sin vocabulario ni flujos de pantalla distintos por marca del EMS.
5. **Antes de campo — instrumento gobernado:** el ciclo natural del estudio incluye **diseño y validación del instrumento** (cuestionario cuantitativo o guía cualitativa). 7Field debe ayudar a **construir, validar y auditar** ese artefacto con un **framework híbrido** (reglas determinísticas + buenas prácticas + IA asistiva + versionado + readiness humano). Esto **no** sustituye el EMS de captura ni convierte a 7Field en “otra app de encuestas”; refuerza **gobierno de la ejecución de investigación** de punta a punta.

---

## Flujo de usuario (alto nivel)

1. **Credenciales del conector**  
   El usuario asocia a su empresa las credenciales del proveedor de campo que use (**Dooblo**, **Qualtrics**, u otros que integremos). Eso habilita las llamadas de lectura permitidas (catálogo, estatus, muestreos analíticos) **sin** sustituir al EMS.

2. **Un GET del mundo Field de la empresa**  
   El sistema **consulta y materializa** la visión canónica 7Field para esa empresa: proyectos / campañas relevantes y su **estatus agregado** (progreso, señales de riesgo recientes, resumen de KPIs donde ya existan datos).

3. **Primera pantalla = estatus de proyectos**  
   El cliente ve **de un vistazo** cómo van los proyectos (o “campañas” en lenguaje de negocio): semáforo o resumen ejecutivo, no dumping de datos.

4. **Drill-down tipo Power BI**  
   Si quiere bajar de nivel, **hace clic en la campaña / proyecto**. Ahí ve la **“salud”** de ese cierre:

   - **KPIs** definidos para el producto (completitud, ritmo, calidad de superficie, cuotas, etc., según el contrato de métricas vigente).
   - **Scores** agregados de riesgo cuando existan en el modelo.
   - **Hallazgos** accionables (qué revisar, qué parar, qué monitorear) con trazabilidad a reglas/versiones donde el sistema lo exija.

5. **Profundización posterior** (no cuenta contra los 3 clics del flujo feliz): export, auditoría, aprobación de hallazgos, Clever sobre bundles ya gobernados, etc.

---

## PRE-FIELD INTELLIGENCE (instrumentación antes del levantamiento)

**Ubicación en producto:** dentro de **7Field**, como capa previa al campo — enlaza con scoring, hallazgos, readiness y costo de error cuando existan en el modelo.

**Idea fuerza:** muchas agencias ejecutan campo bien; **pocos sistemas gobiernan bien el diseño del instrumento**. Ahí nacen sesgos, retrabajo y datos basura. Esta capa puede volverse **tan o más estratégica** que el monitoreo en ejecución si se instrumenta con disciplina.

### Principio de diseño (no negociable)

| Afirmación | Implicación |
|------------|-------------|
| **7Field no es** una app de encuestas ni una plataforma de scripting genérica | La UX no compite con EMS de scripting ilimitado |
| **7Field no “crea preguntas”** como contenido metodológico autónomo | **Sí** crea y preserva **lógica metodológica**, **estructura**, **consistencia** y **control** |
| **La IA asiste** | Acelera, propone borradores, mejora redacción, detecta problemas |
| **La IA no decide sola la metodología** ni publica sin gate humano | Metodología recomendada y reglas vienen de **framework + humano** |

### Framework híbrido (clave)

No solo IA; no solo reglas. **Sí:** framework metodológico explícito **+** reglas determinísticas **+** IA asistiva **+** aprendizaje donde aplique **+** trazabilidad y versionado.

### Flujo macro (previo y durante programa)

**Brief → scripting guiado → revisión manual → QA / errores → listo para campo → levantamiento → pérdidas y calidad en ejecución**

(La parte “campo → pérdidas” sigue siendo el Field operativo ya descrito arriba; PRE-FIELD cubre lo anterior al despliegue.)

### Árbol de módulos PRE-FIELD

```
PRE-FIELD INTELLIGENCE
├── Instrument Builder
├── Framework Library / Framework Engine
├── Auto QA
├── Readiness Gate
├── Versioning
└── AI Assistance
```

### Instrument Builder

Construcción **estructurada** de cuestionarios, screeners, guías cualitativas, mystery shopper, backchecks, incluyendo:

- **Secciones:** introducción, consentimiento, screener, bloques temáticos, demográficos, cierre.
- **Tipos de ítem (ejemplos):** single choice, multi choice, matrix, open end, escala, ranking.

El builder debe guiarse por **tipo de estudio** y **objetivo de negocio** (ver siguiente apartado), no por lienzo en blanco indefinido.

### Tipos de estudio guiados (ejemplos iniciales)

Al iniciar un instrumento, el usuario elige categorías como: **CX**, **U&A**, **Brand Tracking**, **Concept Test**, **Mystery Shopper**, **Focus Group** — el sistema recomienda **framework metodológico** y recorrido **Brief → construcción guiada → Auto QA → Readiness**.

### Framework Engine (valor diferencial)

**No son preguntas sueltas.** Son **plantillas metodológicas**, patrones y heurísticas verificables.

**Ejemplo (CX):** el framework puede exigir o recomendar patrones verificables del tipo: experiencia reciente, touchpoint, satisfacción, fricción, recomendación — como **estructura y consistencia**, no como texto libre sin control.

### Auto QA (pilar comercial fuerte)

Detecta y clasifica problemas; resultado orientado a acción.

**Ejemplos bloqueantes:** lógica rota, skips imposibles, duplicaciones graves, inconsistencias que rompen medición.

**Ejemplos informativos:** pregunta larga, posible sesgo, exceso de matrices, mejoras de claridad.

**Severidades de referencia para producto:** `STOP` · `FIX_NOW` · `MONITOR` (el catálogo fino vive en especificación del motor de reglas).

### Readiness Gate

La IA **no publica sola**. Secuencia conceptual obligatoria:

`[ QA sin bloqueantes críticos ] → [ aprobación humana ] → [ ready for field ]`

### Versionado y auditoría

Cada **instrumento**, conjunto de **reglas** aplicables y **scoring** asociado debe poder auditarse: versiones (`Questionnaire v1.2`), `approved_by`, `approved_at`, `rule_version`, historial de cambios.

### Clever (relación con PRE-FIELD)

Clever **no** debe ser la autoridad que “escribe el cuestionario desde cero”. En el ciclo, Clever encaja mejor **después**, para **resumir**, **explicar**, **proponer mejoras narrativas** y **convertir findings en narrativa** sobre bundles ya gobernados — alineado con [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md).

### Posicionamiento

**7Field es un sistema de gobierno de la ejecución de investigación (*Governance of Research Execution*)**: instrumento + campo + hallazgos + versionado, sin confundirse con un EMS ni con un simple BI.

---

## Roadmap de narrativa comercial (orden acordado)

**Importante:** no vender primero solo PRE-FIELD. Orden de madurez / historia comercial:

1. **Field Control** — monitoreo y salud en ejecución.
2. **Auto QA** del instrumento — pilar fuerte *antes* del campo (encaja en PRE-FIELD Intelligence).
3. **Backcheck Intelligence**.
4. **Cost of Error**.
5. **Clever** — inteligencia ejecutiva sobre artefactos ya gobernados.

PRE-FIELD Intelligence habita **dentro** de 7Field; su **Auto QA** es explícitamente el escalón **2** de esta historia.

---

## Implicación para ingeniería y diseño

### Conectores y dominio canónico

- **Un solo mapa mental en producto:** proyecto Field → estatus / drill-down → KPIs + score + hallazgos. El proveedor externo no define una segunda “app” ni otra jerarquía de navegación.
- **Dominio interno único:** IDs canónicos, KPIs, hallazgos, sync runs y snapshots hablan de **campo y negocio** (progreso, cuotas, calidad de superficie, etc.), no de nombres de endpoints del EMS.
- **Conector delgado:** cada plataforma implementa el mismo contrato abstracto — *autenticar → enlazar encuesta/proyecto externo → traer muestra o agregados permitidos → normalizar* — y escribe en el modelo Field (`FieldProjectExternalSource`, etc.). La capa de decisión y la UI consumen **datos ya normalizados** (o agregados internos), no bifurcan la narrativa por vendor.
- **Transparencia sin duplicar captura:** el usuario debe ver **cuándo** se actualizó la vista, **qué fuente** alimenta cada proyecto y si el pipeline falló o está desfasado; eso refuerza la confianza en “lo que está pasando en el campo” sin convertir 7Field en pantalla de edición del EMS.
- **Implementación:** puede haber rutas o jobs nominados a un vendor mientras exista solo ese conector; la dirección es **interfaces explícitas por `source_type`** y UX única. Evitar que reglas o pantallas queden acopladas a un solo nombre de API en el contrato mental del usuario.
- **APIs y jobs** deben servir primero ese recorrido: *listado + estatus → detalle de proyecto → KPIs + score + findings*, siempre **multi-tenant** y sin exponer más datos crudos de los necesarios para explicar el semáforo.
- **Nuevas features** se aceptan si **encajan en la jerarquía** “Usuario → empresa → proyecto/campaña → salud (KPI + score + hallazgos)” o si son conectores; también si fortalecen **PRE-FIELD** como **gobierno del instrumento** (framework + QA + versionado + gate humano) **sin** sustituir al EMS ni improvisar metodología sin trazabilidad. Se rechazan (o se posponen) si convierten 7Field en **otra pantalla de captura** sustitutiva del cliente.
- Los **3 clics** son **criterio de UX y de demo**: si una historia de usuario no puede demostrarse en ese marco, hay que recortar o reproyectar.

### Paridad Qualtrics ↔ Dooblo (objetivo explícito)

- **Objetivo de producto:** misma **experiencia operativa** donde aplique (credenciales por empresa, fuentes externas, overview de salud, narrativa de “qué fuente alimenta qué proyecto”) y **paridad progresiva** en **capa analítica / decisión** cuando el modelo de datos del EMS lo permita.
- **Estado de referencia (línea base):** Qualtrics cuenta con credenciales por tenant, validación remota (`probe`), vínculos externos y reflejo en overview; el **análisis automático profundo** análogo al pipeline Dooblo (muestras tabulares, cuotas, GPS, motor de hallazgos donde exista) es **trabajo explícito de backlog** hasta declararse cerrado — sin maquillar paridad antes de tiempo.

### No confundir: lista CRUD vs overview

| URL | Respuesta |
|-----|-----------|
| `GET /api/v1/field/projects?company_id=3` | Lista **plana** de proyectos (solo `FieldProject`: nombre, `client_id`, `status`, `ingest_mode`, fechas…). **No** incluye semáforo ni KPIs. |
| `GET /api/v1/field/projects/overview?company_id=3` | Una **fila enriquecida por proyecto**: `health`, `health_reasons`, `kpis_latest`, hallazgos abiertos por severidad, última corrida de análisis, etc. |
| `GET /api/v1/field/projects/{id}/overview` | **Drill-down** de un proyecto (misma fila + `top_findings`). |

En Swagger / OpenAPI, el overview está en el tag **Siete Field** (no sustituye a `GET /projects`).

**Cliente final (B2B2B):** la empresa de investigación (tenant `company_id`, p. ej. Alpha) crea **clientes finales** (`end_clients`: p. ej. Pepsi Dominicana). Cada proyecto Field lleva `client_id` apuntando a ese end client **de la misma empresa**. En overview: `client_display_name` usa **`external_ref`** si existe (clave operativa); si no, **`name`**. `client_name` y `client_external_ref` desglosan ambos campos. Si el `end_client` no pertenece al mismo `company_id` que el proyecto, el vínculo se considera inválido y se muestra `Cliente #id` para forzar corrección de datos.

---

### Contrato API mínimo (mapeo a 3 clics)

| Clic lógico | Qué hace el usuario | Backend (prefijo típico `/api/v1/field`) |
|-------------|---------------------|-------------------------------------------|
| **1** | Entra y deja listo el conector | Credenciales por proveedor, mismo contrato mental: Dooblo `PUT /field/dooblo/credentials`; Qualtrics `PUT /field/qualtrics/credentials` (token cifrado) + `GET /field/qualtrics/status` (`probe=true` valida contra API); prefijo `/api/v1/field`. |
| **2** | Ve **estatus de todos los proyectos** / campañas (semáforo, KPIs ligeros) | `GET /projects/overview` — una sola respuesta agregada por tenant (filtros `company_id` / `client_id` si aplica). |
| **3** | Hace drill-down en **una** campaña / proyecto (“Power BI”) | `GET /projects/{id}/overview` — salud + últimos KPIs + conteos de hallazgos + **muestra corta** de hallazgos abiertos (sin sustituir el listado paginado de `decision-layer/findings` si el usuario profundiza). |

**Profundización** (no cuenta en los 3 clics): sync/análisis (`POST .../sync`, `POST .../decision-layer/...`), KPIs aislados, snapshot operacional, aprobación de hallazgos, export, Clever.

**Scores agregados** (`FieldScore` / fórmula única): cuando existan en modelo, deben colgarse del mismo `GET /projects/{id}/overview` o documentarse aquí en una línea cuando se implemente.

---

## Documentación relacionada (detalle)

- PRE-FIELD Intelligence (builder, framework, Auto QA, readiness, API blueprint): [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md)
- Estrategia y pilares comerciales: [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md)
- Gobierno de hallazgos, criticidad operativa, Clever: [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)
- Contrato mínimo de plataforma: [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md)
- Decisiones estructurales cerradas (motor de reglas, estudios, etc.): [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md)
- Ecosistema e ingest CSV cuando aplique: [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md) · [FIELD_CSV_2026_1.md](FIELD_CSV_2026_1.md)

---

## Versionado

- **v1–v1.4 (2026‑02‑23 → 2026‑05‑02):** versiones anteriores con mapas de capas, fases A–E, tracción por fase y sección 9 honestidad repo (archivo histórico en git).
- **v2 (2026‑05‑02):** reescritura **simple**: premisa “no replicar captura”, flujo credenciales → GET empresa → estatus → drill campaña → salud (KPI + score + hallazgos), **regla de 3 clics**; detalle profundo movido a documentos enlazados.
- **v2.1 (2026‑05‑02):** tabla **Contrato API mínimo** (3 clics) + nota scores; alineación con endpoints reales (`/projects/overview`, `/projects/{id}/overview`).
- **v2.2 (2026‑05‑02):** tabla **No confundir** `GET /projects` vs `GET /projects/overview`; Swagger en `list_projects` apunta al overview.
- **v2.3 (2026‑05‑02):** overview B2B2B — `client_display_name` desde `external_ref` o `name`; validación `end_clients.company_id` = `project.company_id`.
- **v2.4 (2026‑05‑06):** premisa **experiencia única** ante cualquier EMS de levantamiento; subsección **Conectores y dominio canónico**; clic 1 del contrato API formulado en genérico multi‑proveedor (paths actuales Dooblo como ejemplo).
- **v2.5 (2026‑05‑06):** backend — credenciales Qualtrics por empresa (`company_qualtrics_settings`), rutas `/field/qualtrics/credentials` y `/field/qualtrics/status`; `source_type` **`qualtrics`** en fuentes externas; tabla clic 1 actualizada.
- **v2.6 (2026‑05‑07):** **PRE-FIELD INTELLIGENCE** — árbol Instrument Builder, Framework Engine, Auto QA, Readiness Gate, Versioning, AI Assistance; principios “7Field no crea preguntas sueltas” / IA no decide metodología sola; framework híbrido; flujo Brief → scripting → revisión → QA → campo; roadmap comercial ordenado (Field Control → Auto QA → Backcheck → Cost of Error → Clever); posicionamiento **Governance of Research Execution**; **paridad Qualtrics ↔ Dooblo** como objetivo explícito de ingeniería con estado/reserva sobre análisis profundo.
- **v2.7 (2026‑05‑06):** enlace a especificación detallada [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md); JSON Schema draft para `instrument_spec` en `examples/instrument_spec_v1.schema.json`.
- **v2.8 (2026‑05‑08):** PRE-FIELD API robusta — revisiones `instrument_spec` persistidas, validación stateless y con auditoría; ver doc PRE-FIELD §7.
