# 7Field — Arquitectura de experiencia (producto)

**Estado:** activo — **documento maestro simple**: describe *qué debe sentir el usuario* y *qué construimos* dentro del **ecosistema Siete** (Field, CX, InS, Clever, Perfil), no solo un módulo aislado. La **norma transversal** de producto, UX/UI y criterio técnico está también en [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md). La **norma obligatoria** ampliada de experiencia Field está en § **Dirección de producto, UX/UI y criterio técnico** (abajo). El **orden de ejecución** para implementación (Cursor) está en [7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md](7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md). El detalle técnico largo y gobierno profundo siguen en los enlaces al final.

---

## Premisas

1. **7Field no replica** Dooblo, Qualtrics ni ninguna herramienta de captura. **Interpreta ejecución** a partir de datos que el cliente ya tiene en esos sistemas (u otros conectores).
2. **Regla de 3 clics:** desde que el usuario entra con intención de ver campo, hasta tener **una lectura clara de “salud”** del negocio de campo, el flujo feliz no debe forzar más de **tres interacciones principales** (p. ej. login/config → lista/estatus → campaña/proyecto elegido). Todo lo demás es **profundización opcional**, no barrera.
3. **“Salud”** aquí significa: **KPIs acordados** + **scores / riesgo** derivados de reglas versionadas y, cuando aplique, **hallazgos** que explican *por qué* algo está en rojo o ámbar — no una tabla infinita de respuestas crudas.
4. **Misma lectura operativa para cualquier proveedor:** Dooblo, Qualtrics u otro sistema de levantamiento solo cambian la **tubería de ingesta**; quien use 7Field debe **entender lo mismo** — qué pasa en campo, salud del proyecto, alertas — sin vocabulario ni flujos de pantalla distintos por marca del EMS.
5. **Antes de campo — instrumento gobernado:** el ciclo natural del estudio incluye **diseño y validación del instrumento** (cuestionario cuantitativo o guía cualitativa). 7Field debe ayudar a **construir, validar y auditar** ese artefacto con un **framework híbrido** (reglas determinísticas + buenas prácticas + IA asistiva + versionado + readiness humano). Esto **no** sustituye el EMS de captura ni convierte a 7Field en “otra app de encuestas”; refuerza **gobierno de la ejecución de investigación** de punta a punta.
6. **Producto ancla y contrato único de observabilidad:** **7Field** es la capa de **control operacional** — QA, readiness, riesgo y gobierno sobre estudios y ejecución de campo — **no** una plataforma de captura. **Principio rector:** todo lo relevante debe poder converger en **hallazgos auditables bajo el mismo contrato** (PRE-FIELD, Field, scoring, IA, Readiness, intelligence ejecutiva). **No** subsistemas aislados sin camino de auditoría compartido. El espinazo comercial sigue siendo **Auto QA → Backcheck Intelligence → Cost of Error → Clever** gobernado; el resto lo refuerza.
7. **Memoria metodológica viva (ecosistema Siete):** Siete **no** es solo APIs + pantallas; es **inteligencia operacional persistida** que Field, CX, InS, Clever y Perfil deben poder **compartir** como contexto (véase [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md) §0 y §10).

---

## Dirección de producto, UX/UI y criterio técnico (obligatorio antes de ampliar superficie)

Norma de equipo: **ninguna feature nueva de superficie** sin pasar por esta sección y por el checklist final. La complejidad puede vivir en backend y modelo; la **superficie** debe cumplir tono, densidad y continuidad aquí descritos.

### Lo que NO construimos

- **No** otro Qualtrics, SurveyMonkey, Dooblo, builder genérico ni pantalla de captura sustitutiva.
- **No** competir en “quién tiene más tipos de pregunta” ni en scripting infinito.

### Tesis del producto

**7Field = capa inteligente de preparación + ejecución + supervisión de investigación.** Interpretamos y gobernamos ejecución sobre datos que el cliente ya tiene en EMS/conectores; **no** reemplazamos el EMS en su fortaleza (captura / scripting).

**Territorio obligatorio del diseño (Cursor / producto):** dejar de mirar **solo** “otro software SaaS”. Combinar de forma explícita:

- **research methodology** (patrones y estándares reales del sector),
- **UX moderna** (ritmo, jerarquía, foco),
- **operational intelligence** (claridad operativa sin consola heredada),
- **AI copilots** (consultivos, no autónomos),
- **premium visual storytelling** (relato del estudio y del participante).

**Percepción objetivo:** la versión **moderna, inteligente y visual** de cómo debería operar investigación en 2026 — **no** otro sistema enterprise genérico de investigación, **no** ERP ni panel administrativo disfrazado.

### Referencias UX/UI (gold standard — estudiar patrones, no copiar literal)

Extraer **sensación, ritmo, densidad, jerarquía y disclosure**; **no** clonar interfaces.

| Referencia | Qué absorber |
|------------|----------------|
| **Notion AI** | IA contextual y humana; “piensa conmigo”; superficie limpia; bloques claros; complejidad oculta; cero sensación ERP. |
| **Linear** | Foco extremo; velocidad percibida; claridad operacional; densidad muy controlada; estados simples; minimalismo premium. |
| **Stripe Dashboard** | Enterprise moderno; jerarquía impecable; spacing premium; complejidad simplificada; cards y summaries fuertes. |
| **Dovetail** | Síntesis de research; narrativa visual; insights; agrupación humana; tono metodológico moderno (**muy relevante PRE-FIELD**). |
| **Maze** | Onboarding guiado; planning legible; lenguaje humano; claridad de flujo. |
| **Airtable Interfaces** | Vistas enfocadas; progressive disclosure; flexibilidad visual; experiencias contextuales (**no** por idolatría tabular). |
| **FigJam / Figma Slides** | Storytelling visual; participant journey; pensamiento en flujo; narrativa. |

### Referencias metodológicas (patrones reales — no teoría académica en superficie)

Tomar **buenas prácticas reconocibles** del ecosistema de investigación y CX; **no** inventar metodología arbitraria ni exponer marcos como manual pesado.

**Estudiar / alinear patrones con:** Ipsos, Kantar, NielsenIQ, Gallup, Bain CX, Qualtrics XM Institute, Forrester Research, ESOMAR, MRS, estándares de UX research, marcos JTBD, marcos de madurez CX — entre otros equivalentes serios.

**Traducción obligatoria a producto:** frameworks → **decisiones guiadas**, recomendaciones simples, señales visuales, mejores prácticas aplicadas, estructura sugerida, warnings útiles, preguntas inteligentes. El usuario debe sentir **“esto me ayuda a pensar mejor”**, no *“estoy leyendo metodología académica”*.

**Tono deseado de la IA/guidance:** mezcla creíble entre **consultor senior + director metodológico + operaciones inteligentes** — siempre **consultivo** y acotado por datos y gates humanos.

### Núcleo y moat (continuidad PRE-FIELD ↔ FIELD)

El núcleo es una cadena continua:

**pensamiento → preparación → ejecución → supervisión → aprendizaje.**

**PRE-FIELD** y **FIELD** deben sentirse como **un solo flujo**, no como módulos desconectados. La **intención metodológica** creada al inicio debe **mantenerse viva** durante el campo.

**Ejemplo (moat):** si el brief habla de onboarding bancario, FIELD debe poder **heredar contexto** sin que el usuario re-explique el estudio en cada pantalla:

- qué bloques eran sensibles,
- dónde se esperaba abandono,
- qué partes pesan más,
- qué riesgos importan,
- qué hallazgos son más relevantes.

### Superficie UX — lo que rechazamos vs lo que buscamos

**No** queremos UX “enterprise pesada”: tablas infinitas, densidad, jerga técnica en primera clase, configuraciones interminables ni **framework visible** como protagonista.

La superficie debe sentirse **clara, premium, moderna, guiada, elegante, humana e inteligente** — más **editorial** que consola operacional. **Lo visual vende:** priorizar whitespace, jerarquía fuerte, cards grandes, summaries, iconografía suave, tipografía respirable, ritmo vertical elegante, **una acción principal** por pantalla. **Reducir:** densidad, grids gigantes, tablas largas, formularios infinitos, labels técnicos en primera línea, bloques enormes de texto, múltiples CTAs compitiendo.

**No:** ERP, consola legacy, software administrativo o panel lleno de tablas como primera experiencia.

**Percepción objetivo (orden):**

1. **“7Field me ayuda a pensar mejor.”**
2. **“7Field me ayuda a ejecutar mejor.”**

**No:** *“estoy operando un sistema complejo”.* En LATAM y mercados similares, el producto también apoya **seniority y consistencia**; eso se transmite por **claridad y guía**, no por declararlo en etiquetas de UI.

### Reglas UX/UI obligatorias

- Menos es más.
- **Progressive disclosure siempre:** JSON, hashes, lineage, paquetes QA y metadata viven en **“Detalles técnicos”** (o equivalente); no en la primera lectura.
- La superficie principal usa **lenguaje humano**.
- **Un objetivo claro por pantalla.**
- Más espacio visual; más tarjetas y resúmenes; **menos tablas** en primera clase.
- Menos badges; menos estados técnicos visibles sin necesidad.
- Más narrativa, más foco, menos ruido.

### PRE-FIELD y FIELD — definición operativa

**PRE-FIELD no es un builder.** Es: copiloto metodológico, guía estructurada, preparación inteligente, claridad operacional.

Debe sentirse como **“estructurar inteligentemente un estudio”**, no como *“configurar un sistema”*. Flujo emocionalmente moderno: explica el problema → guidance contextual → recomendaciones → ajusta estructura sugerida → visualiza journey → revisa → aprueba → publica/exporta.

**FIELD no es solo monitoreo.** Es: continuidad contextual del estudio, supervisión alineada a la intención, lectura inteligente de la ejecución.

Debe sentirse como **“ejecutar con contexto”**: **no** dashboards genéricos desconectados. FIELD debe reflejar **qué era importante**, **qué riesgos vigilar**, **qué partes eran críticas**, **qué hallazgos pesan más** y **qué merece atención** para **este** estudio.

### IA — criterio obligatorio

**No construir:** chatbot infinito; generación descontrolada; cuestionarios completos autónomos; “AI magic” caótico.

La IA correcta es **contextual, metodológica, consultiva, operacional y accionable**. Debe sentirse como **seniority encapsulado** y **copilot senior**, **no** como autonomía fuera de control ni “AI magic”.

**Ejemplos de tono correcto:**

- “Detectamos posible fatiga.”
- “El bloque demográfico aparece demasiado temprano.”
- “La pregunta de negocio no está reflejada.”
- “Esperábamos fricción aquí y el abandono es mayor.”
- “Las respuestas abiertas sugieren ansiedad.”

### Contrato análisis (backend) ↔ presentación (frontend)

**Backend** (motores de reglas, validación de esquema, QA, heurísticas, scoring, IA acotada donde aplique) es responsable de **analizar** el instrumento y el contexto del estudio y de producir salidas **auditables**. Dimensiones de referencia (no exhaustivas; el catálogo fino vive en especificación del motor):

- **longitud** (instrumento, bloques, ítems),
- **fatiga** (carga y ritmo para quien responde),
- **sesgo** (formulación, orden, priming / leading),
- **redundancia**,
- **orden** (secuencia frente a intención metodológica y de negocio),
- **consistencia** (lógica, saltos, coherencia interna),
- **cobertura metodológica** (alineación con brief, tipo de estudio y framework vigente),
- **validaciones** (esquema, reglas QA, gates),
- **riesgos operacionales**.

**Frontend** **no** debe duplicar ese análisis para “simular” inteligencia: **solo presenta insights en lenguaje humano** (tarjetas, callouts, narrativa del recorrido) a partir de datos y resultados ya calculados en API/backend — más **mapear, ordenar y copy** que motor nuevo. El detalle técnico (reglas, hashes, JSON, lineage) permanece en **«Detalles técnicos»** u equivalente.

### Dirección visual futura — Journey Intelligence

El siguiente salto **no** es drag/drop complejo ni un builder gigante como protagonista.

El **wow correcto** es: pegar un brief → estructura inteligente → **visualizar el recorrido del participante** → detectar riesgos → sugerencias útiles → pasar **naturalmente** a campo → que **FIELD entienda ese contexto**.

Producto visual objetivo: **Journey Intelligence** (preview elegante del recorrido, narrativa del participante, riesgos contextuales, señales automáticas, continuidad viva en Field, insights accionables, sensación de acompañamiento). Ver también premisa de **regla de 3 clics** arriba y demo corta de confianza.

### Angular — reglas técnicas (frontend)

**Arquitectura:**

- Contenedores “smart” + componentes presentacionales “dumb”.
- Componentes **pequeños** y reutilizables.
- **Helpers de copy** separados del markup cuando crezca el texto.
- Signals / `computed` limpios; **evitar mega-components**.

**Primitivas y experiencias dedicadas** (evitar reciclar layouts “admin” genéricos como base visual): `field-hero-card`, `field-guided-step`, `field-insight-card`, `field-empty-state`, `field-checklist`, `field-next-step-banner`, `field-participant-journey-preview`, y hacia donde apunte el roadmap: `guided-brief-flow`, `framework-recommendation-cards`, `insight-callouts`, `study-review-experience`, `operational-priority-cards` (nombres orientativos; selectores Angular coherentes con el repo).

**Evitar:** templates enormes llenos de `@if`; lógica de IA mezclada en HTML; **heurísticas de instrumento duplicadas** que debieran vivir en backend (ver § Contrato análisis backend ↔ frontend); helpers gigantes; interfaces duplicadas; tablas complejas en superficie; utilities Tailwind caóticos repetidos.

**Sistema visual:** spacing consistente; tipografía que respire; menos bold; menos uppercase; menos ruido visual.

### Python / IA / backend

**No** usar IA para **reemplazar** criterio humano ni gates de publicación.

**Sí** usar: heurísticas; clasificación contextual; extracción de intención; agrupación semántica; riesgos metodológicos; señales operacionales; resúmenes ejecutivos. Preferir **recomendaciones pequeñas y accionables** sobre generación masiva.

Python para: heurísticas metodológicas, scoring, señales, NLP liviano, embeddings, clasificación, clustering, detección de patrones, resúmenes — **sin** pipelines gigantes prematuros.

El **contrato** frente al frontend está en § **Contrato análisis (backend) ↔ presentación (frontend)** arriba: el análisis profundo vive aquí; la UI solo humaniza lo ya derivado.

Preferir **servicios pequeños**, outputs **auditables**, **prompts acotados**, **reglas explícitas + IA contextual**.

### Checklist obligatorio antes de agregar cualquier feature

Preguntar siempre:

1. ¿Ayuda a **pensar mejor**?
2. ¿Ayuda a **ejecutar mejor**?
3. ¿**Mantiene continuidad** PRE-FIELD ↔ FIELD?
4. ¿**Se ve premium** y **se siente inteligente**?
5. ¿**Reduce complejidad visible** (sin sacrificar rigor debajo)?
6. ¿Genera **confianza rápida** y podría **sorprender positivamente** en demo de ~3 minutos?

Si no cumple: **iterar** antes de ensanchar superficie.

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

### Flujo PRE-FIELD en tres capas (experiencia objetivo)

La pantalla / producto **PRE-FIELD** queda **oficialmente** organizado en tres frentes — sin saltarse etapas ni mezclar brief con instrumento técnico ni IA sin marco:

| Capa | Nombre oficial | Propósito | Principio |
|------|----------------|-----------|-----------|
| **1** | **Brief** | Entender **todo lo que el cliente desea** (brief contratable): objetivos, público, hipótesis, restricciones, entregables, tipo de estudio tentativo. | No avanzar a instrumentación hasta brief **suficiente** (mínimos por tipo + score + aprobación humana). |
| **2** | **Técnico / instrumento versionado** | **Versionado**, **asignación** a estudio/proyecto Field (tenant, cliente), `instrument_spec`, Framework Library, validación de esquema, Auto QA, Readiness L4. | Auditabilidad y modelo canónico; sin improvisación fuera de revisiones. |
| **3** | **Inteligencia + Banco de guías** | Sugerencias acotadas al **framework explícito** (y waivers ligados a **revisión**); biblioteca reutilizable tras aprobaciones; ver [ADR 001](adr/001-pre-field-brief-framework-ai-guide-bank-governance.md). | La IA **complementa** criterio humano; **no** decide método solo; UX **operacional y auditada**, no “AI playground”. |

La ingeniería actual cubre **sobre todo la capa 2**. Las capas **1 y 3** y el banco son roadmap de datos y políticas; **prioridad inmediata**: consolidar snapshots, hashes, lineage, gates servidor, trazabilidad IA y metadata de storage **antes** de ampliar superficie visual (orden **A→G** en ADR y modelo canónico).

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

- **Secuencia de ejecución (Cursor) — orden obligatorio 1→9:** [7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md](7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md)
- PRE-FIELD — **gobierno cerrado** (ADR): [adr/001-pre-field-brief-framework-ai-guide-bank-governance.md](adr/001-pre-field-brief-framework-ai-guide-bank-governance.md)
- PRE-FIELD — **modelo canónico** (entidades, gates, bounded contexts): [7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md](7FIELD_PRE_FIELD_CANONICAL_MODEL_V1.md)
- PRE-FIELD Intelligence (builder, framework, Auto QA, readiness, API blueprint): [7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md)
- **Backend — motor de inteligencia de estudio** (recommendation engine, insights, QA heuristics, interpretación operativa, journey/fatiga/scoring, prompts centralizados, EMS): [7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md](7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md)
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
- **v2.8 (2026‑05‑08):** PRE-FIELD API robusta — revisiones `instrument_spec` persistidas, validación stateless y con auditoría; ver **[7FIELD_PRE_FIELD_INTELLIGENCE_V1.md](7FIELD_PRE_FIELD_INTELLIGENCE_V1.md) §7** (API REST `/api/v1/field`).
- **v2.9 (2026‑05‑08):** motor Auto QA bootstrap **QA_RULE_001–005** (`instrument_qa_runtime`) + histórico `field_instrument_qa_runs`.
- **v3.0 (2026‑05‑09):** **Readiness Gate L4** — políticas de bloqueo por empresa, signatarios opcionales obligatorios, firmas con snapshot y estado `approved` en revisión.
- **v3.1 (2026‑05‑11):** PRE-FIELD — **flujo explícito en tres capas** (brief → técnico/versionado → inteligencia asistida acotada a framework) + **banco de guías** tras aprobación cliente; alineación roadmap vs implementación actual (capa 2 prioritaria).
- **v3.2 (2026‑05‑11):** PRE-FIELD — **ADR 001** (brief, framework obligatorio, trazabilidad IA, banco de guías, gates) + **modelo canónico** enlazado desde esta doc maestra.
- **v3.3 (2026‑05‑11):** Principio **hallazgos auditables mismo contrato** (premisa 6); PRE-FIELD nombres oficiales tres capas; prioridad **A→G** y waiver por revisión remitidos a ADR/modelo canónico.
- **v3.4 (2026‑05‑06):** **Estrella norte** — continuidad PRE-FIELD ↔ FIELD como un solo flujo inteligente (intención viva en campo); anti‑patrones UX vs dirección deseada; rol consultivo de la IA; checklist por pantalla/feature; demo wow correcto; percepción “capa inteligente” sin competir en captura; consistencia con seniority LATAM vía producto, no copy explícito.
- **v3.5 (2026‑05‑06):** prioridad del **siguiente salto visual/producto**: recorrido preview + narrativa participante + riesgos contextuales + señales automáticas + continuidad viva en Field + insights accionables + acompañamiento — explícitamente **no** drag/drop/builder como eje del valor.
- **v3.7 (2026‑05‑06):** playbook **[7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md](7FIELD_CURSOR_EXECUTION_SEQUENCE_V1.md)** — secuencia obligatoria Journey Intelligence → preview visual → continuidad PRE‑FIELD→FIELD → IA consultiva → UX → progressive disclosure → Angular → Python → regla de percepción; enlace desde cabecera y documentación relacionada.
- **v3.9 (2026‑05‑16):** § **Contrato análisis (backend) ↔ presentación (frontend)** — backend analiza longitud, fatiga, sesgo, redundancia, orden, consistencia, cobertura metodológica, validaciones y riesgos operacionales; frontend solo presenta insights humanos (sin duplicar motor).
- **v4.2 (2026‑05‑16):** P2 parcial — persistencia **`field_participant_journeys`** + **`field_journey_phases`** al responder `study-intelligence`; migración `p9q8r7s6t5u4`; API devuelve `participant_journey_snapshot_id`.
- **v4.1 (2026‑05‑16):** **`GET /field/instrument-revisions/{revision_id}/study-intelligence`** — motor Study Intelligence (journey, QA instantáneo, Readiness, insights); ver `7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md` v1.1 y `7FIELD_PRE_FIELD_INTELLIGENCE_V1.md` §7.
- **v4.0 (2026‑05‑16):** blueprint **[7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md](7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md)** — capas recommendation / insights / QA / operacional / facade `StudyIntelligenceService`; entidades `participant_journey`, `journey_phase`, `operational_risk`, `methodological_signal`, `fatigue_risk`, `sensitivity_area`, `expected_dropout_zone`, `insight_priority`; **prompt registry** centralizado (`app/study_intelligence/prompt_registry.py`); continuidad PRE‑FIELD→FIELD; exportadores y mappings EMS en servidor; contratos Python `app/study_intelligence/contracts.py` (P0).
