# 7Field — Dirección de experiencia de producto (v1.3)

**Tipo:** criterio transversal (producto, diseño, frontend, backend, IA).  
**Tiempo de lectura:** ~8 minutos.  
**Uso:** citar en PRs y decisiones de alcance; no sustituye especificaciones técnicas detalladas.

---

## 0. Tesis fundacional — Siete es memoria metodológica viva

**Siete no es** un conjunto de APIs conectadas a pantallas ni “productos” solo por flags de menú.

**Siete es** una **memoria metodológica viva**: inteligencia operacional **persistida**, **versionada** y **compartida**, de la que cada módulo (Field, CX, InS, Clever, Perfil) es una **vista especializada** sobre el mismo contexto.

Implicaciones:

- El valor está en **convertir inteligencia en memoria** (señales, scores, journey, expectativas, hipótesis, riesgos) que **sobrevive** al flujo que la generó — no en pantallas aisladas.
- El backend **no se define** como REST CRUD genérico; es **orquestación, políticas, inteligencia, tenant y continuidad** con APIs como superficie.
- La IA **guía y acelera criterio humano**; **no** sustituye al investigador ni produce “estudios mágicos” ni automatización opaca.

7Field es la pieza **ancla** que más claramente une **preparación (PRE-FIELD)** y **ejecución (FIELD)**; el resto del ecosistema consume la misma línea de memoria cuando el contrato de datos lo permite.

---

## 1. Qué es 7Field

7Field es la **capa inteligente sobre la operación de investigación**: conecta **lo que el estudio intenta descubrir** con **lo que realmente ocurre en campo**, de forma continua y auditable — como parte de esa **memoria viva**, no como módulo suelto.

**7Field no es:**

- Otro Qualtrics (builder infinito de cuestionarios).
- Otro EMS/tablero enterprise genérico de métricas sueltas.
- Una consola donde el usuario debe aprender primero el modelo de datos interno.

**7Field sí es:**

- Un sistema que **reduce fricción cognitiva** antes del levantamiento y **aclara prioridades** durante la ejecución.
- Un producto donde la sensación dominante es **inteligencia y claridad**, no complejidad administrativa.

---

## 2. Los dos mundos

Dos contextos cognitivos **distintos**, no dos pestañas del mismo panel operativo.

| Contexto | Rol | Sensación buscada |
|----------|-----|-------------------|
| **PRE-FIELD** | Diseño inteligente del estudio | Editorial, estratégica, espaciosa, guiada |
| **FIELD** | Supervisión inteligente de ejecución | Operativa, rápida, ejecutiva, monitoreo |

**PRE-FIELD responde (intención):**

- Qué queremos aprender y con qué enfoque.
- Cómo se vivirá el estudio desde la perspectiva del participante.
- Qué riesgos o tensiones metodológicas aparecen **antes** de salir.

**FIELD responde (realidad):**

- Cómo está ejecutándose realmente el levantamiento.
- Dónde hay fricción, alertas o incumplimientos.
- Dónde la ejecución **se aleja de la intención** acordada en diseño.

---

## 3. El puente (moat)

El diferencial competitivo no es cada pantalla por separado: es la **continuidad inteligente** entre diseño y campo.

Lo que PRE-FIELD detecta — **fatiga probable, sesgo, bloques sensibles, abandono esperado, preguntas débiles, riesgo metodológico**, hipótesis, journey diseñado — **no puede morir dentro de PRE-FIELD**. Debe **materializarse** en artefactos que el sistema **persiste** y FIELD **consume**, por ejemplo:

- **signals** y **methodological_signal** (vocabulario de dominio; ver motor backend).
- **contextual_scores** (dimensiones de riesgo / calidad / alineación con **versionado de fórmula** donde aplique).
- **journey intelligence** y fases esperadas vs lectura operativa.
- **operational expectations** (qué se esperaba observar, qué preocupaba, qué era sensible).
- **study intelligence persistido** y snapshots con **lineage** — no solo la última pasada en memoria de sesión.

**FIELD no puede comportarse** como si el estudio **naciera** cuando llegan respuestas. FIELD debe entender **qué se esperaba**, **qué preocupaba**, **qué era sensible**, **qué hipótesis existían**, **qué journey se diseñó** y **qué riesgos ya habían sido detectados** — comparando ejecución contra esa **memoria**, no contra vacío.

**FIELD debe entender lo que PRE-FIELD intentó lograr**, mediante:

- **Contexto persistente** (no solo “última métrica”).
- **Journey intelligence** y lectura del recorrido esperado vs señales reales.
- **Riesgos esperados** y puntos sensibles acordados en diseño.
- **Sensibilidad metodológica** (tono, carga, orden, advertencias).
- **Lineage y versionado** que permitan confianza enterprise (“qué versión del estudio está viva en campo”).

Sin ese puente, 7Field se siente como **módulos conectados**. Con él, se siente como **un sistema unificado** y como **memoria viva**.

---

## 4. Modelo mental del usuario

Las **siete preguntas humanas** que la experiencia debe poder responder, en orden cognitivo natural:

1. **¿Qué queremos aprender?** (negocio / decisión)
2. **¿Qué metodología encaja?** (enfoque recomendado, sin dogmatismo opaco)
3. **¿Cómo se verá la experiencia del participante?** (recorrido, claridad, respeto al respondiente)
4. **¿Qué podría salir mal antes de salir?** (riesgos, sensibilidad, calidad del instrumento)
5. **¿Estamos listos para salir a campo?** (readiness entendible, sin checklist técnico expuesto)
6. **¿Cómo va el campo ahora?** (salud, ritmo, cobertura, calidad viva)
7. **¿Dónde intervenir ya?** (priorización accionable, no ruido)

Si una sola pantalla intenta responder más de una pregunta fuerte, la experiencia **colapsa**.

---

## 5. Principios UX/UI

- **Una pantalla → una pregunta mental dominante.**
- **Menos tablas como protagonistas**; más jerarquía, ritmo y lectura en escaneo.
- **Más narrativa visual** (bloques claros, progresión, estado del estudio).
- **Progressive disclosure agresivo**: lo avanzado existe, pero no compite con lo esencial.
- **Premium y simple a la vez**: rápido de usar, sin sensación de “portal corporativo pesado”.
- **Lenguaje humano** en titulares y ayudas; la jerga técnica no es el vocabulario del cliente.
- **IA contextual y consultiva**: acelera criterio y detecta riesgos; no sustituye el juicio del equipo.
- **Complejidad escondida**: lo metodológico fuerte vive detrás de superficies claras.

**Contraste de percepción (ejemplos):**

| Mal (idioma interno) | Bien (pregunta humana) |
|----------------------|-------------------------|
| “Revision readiness QA consistency” | “¿Qué podría afectar la salida a campo?” |
| “Instrument spec validation stale” | “¿Este borrador sigue alineado con lo último que revisamos?” |
| “Blocking codes aggregate_status” | “¿Qué nos falta para dar el visto bueno?” |
| “Study intelligence bundle” (en UI) | “Qué detectó el sistema sobre tu estudio” |

---

## 6. Anti-patrones

Evitar activamente:

- **Dashboards enterprise pesados** como plantilla por defecto.
- **Builders infinitos** tipo taller de encuesta clásica.
- **Jerga técnica visible** (IDs internos, nombres de subsistemas, mensajes de runtime).
- **Múltiples verdades** sin jerarquía (“esto dice una cosa y aquello otra” sin explicación).
- **Pantallas híbridas** que mezclan diseño metodológico y monitoreo operativo en el mismo layout mental.
- **Frontend inventando metodología o severidades**: la inteligencia debe venir del backend como fuente de verdad.

---

## 7. Dirección técnica

### Frontend (Angular — p. ej. Vercel)

**Responsabilidad:** experiencia, navegación, **copiloto visual**, visualización, interacción humana, **storytelling operacional**.

**No:** inteligencia pesada, heurísticas metodológicas centrales, scoring principal, ni duplicar políticas que deben vivir en servidor.

- **Shells separados** para PRE-FIELD y FIELD (distinta energía, navegación y copy).
- **Componentes por intención de usuario** (brief, metodología, journey, riesgos, readiness, salud, alertas), no mega-componentes “que lo hacen todo”.
- **Presentation-first**: vistas legibles; contenedores pequeños; estado derivado claro (p. ej. signals/computed).
- **Backend-driven intelligence**: el cliente muestra; no reinterpreta reglas de negocio metodológicas.

### Backend (FastAPI — cerebro operacional)

FastAPI debe ejercer de forma explícita (aunque evolucione por fases):

- **API gateway** y superficie HTTP coherente con el contrato de plataforma.
- **Orchestration layer** (ensamblar lecturas, pipelines, bundles).
- **Intelligence layer** (motor de estudio, QA, journey, señales).
- **Policy layer** (gates, readiness, permisos de negocio alineados a tenant).
- **Memory layer** (persistencia de intención, snapshots, lineage, aprobaciones).
- **Tenant-aware context** (mismo estudio visto con límites correctos por empresa/usuario).

**No** reducir mentalmente el backend a “CRUD de tablas”: los endpoints son **vistas sobre memoria y política**, no el modelo mental completo.

### Workers y cómputo asíncrono (dirección)

Operaciones pesadas o lentas (p. ej. **Whisper**, embeddings, análisis semántico extenso, pipelines de QA/scoring masivos, clustering) deben tender a **workers Python asíncronos dedicados**, separados del request path síncrono — **cuando la infra lo adopte**. La lista orientativa incluye: transcripción, embeddings, análisis semántico y de journey, heurísticas batch, QA, scoring, clustering, extracción de insights, contextual analysis, recommendation pipelines.

**Regla:** no implementar colas/workers “por imaginación”; validar con repo e infra reales.

### Persistencia

- **PostgreSQL:** verdad operacional — contratos, snapshots, lineage, approvals, findings, decisiones, estado canónico.
- **Vector store (horizonte):** **pgvector** en Postgres y/o motor dedicado (**Qdrant**, **Weaviate**, u otro) para **recordar, comparar, reutilizar patrones**, recuperar contexto, similitud y recomendaciones — siempre con gobierno y tenant claros.

### IA en plataforma

- **Elevar criterio**, reducir errores, acelerar thinking, sugerir buenas prácticas.
- **Detectar riesgos** y mantener consistencia con lo ya definido.
- **No reemplazar** el rol del investigador ni prometer “cuestionarios mágicos”, automatización descontrolada ni experiencias impredecibles.

**Arquitectura AI-first (dirección):**

- **No prompts sueltos** en servicios: **prompt registry** por vertical (`field/`, `cx/`, `ins/`, `clever/`, `perfil/` — estructura objetivo en repo) con **versionado, trazabilidad, tests**, plantillas reutilizables y observabilidad.
- **LLM router / multi-proveedor** (OpenAI, Anthropic, Gemini, fallback futuro): **no atar** el negocio a un solo proveedor; diseño incremental según contrato y secretos del equipo.

El estado actual del código puede ser más simple; las PRs deben **acercar** estas prácticas sin fingir piezas que no existen.

---

## 8. Secuencia de evolución

Orden deliberado para **no rehacer todo sin dirección** ni ensanchar superficie sin núcleo:

1. **Navegación y modelo mental** — Separación clara FIELD → PRE-FIELD / FIELD; shells, lenguaje y ritmo visual distintos.
2. **Pregunta mental → pantalla** — Mapear cada flujo crítico a una pregunta dominante; cortar híbridos.
3. **Convergencia del intelligence bundle** — Un núcleo coherente que alimente preview, riesgos y readiness con la misma historia.
4. **FIELD contextual** — Supervisión que **muestre intención persistida** frente a ejecución (no solo KPIs aislados).

---

## 9. Checklist obligatorio para PRs / features

Antes de aprobar o mergear, la persona revisora debe poder responder **sí** de forma honesta (producto + ingeniería):

**Continuidad y núcleo**

1. **¿Fortalece la continuidad inteligente** (PRE-FIELD ↔ FIELD y, cuando corresponda, consumo de **memoria metodológica** por CX / InS / Clever / Perfil), o solo añade superficie o datos sueltos?
2. **¿Convierte inteligencia en memoria viva** (persistida, trazable, reusable por FIELD u otros consumidores), en lugar de dejar insights “encapsulados” en un solo paso o pantalla?
3. **¿Ayuda a pensar mejor** y **a ejecutar mejor** el usuario objetivo?
4. **¿Reduce caos operacional** sin añadir automatización barata o impredecible?

**Superficie y honestidad del sistema**

5. **¿La vista tiene una pregunta mental dominante clara**, o mezcla diseño y operación / varias decisiones a la vez?
6. **¿El texto visible está en lenguaje humano**, sin exponer jerga interna salvo herramientas explícitas de administración?
7. **¿La inteligencia mostrada viene del backend / bundle coherente**, sin que el frontend “infiera metodología” ni scoring principal?
8. **¿Se aplicó progressive disclosure** (lo esencial primero; lo avanzado accesible pero no competitivo)?
9. **¿Evitamos anti-patrones** de la sección 6 (híbrido enterprise, builder mindset, múltiples verdades)?

**Percepción**

10. **¿Se siente premium y simple** a la vez, **wow útil** en poco tiempo, y como **inteligencia real** — no como automatización superficial?

Si la respuesta honesta es “no” en más de un bloque, **detener o recortar** antes de seguir acumulando complejidad.

---

## 9bis. Rol de Cursor y rol de producto

**Cursor / agentes de código** implementan, estructuran, refactorizan y aceleran entrega **según** esta dirección y los docs canónicos.

**No sustituyen:** visión de producto, UX definitiva, moat, diferenciación, narrativa, priorización de moat PRE-FIELD ↔ FIELD, ni decisión explícita de políticas IA sensibles.

Si falta criterio: **escalar a humanos de producto** o **atesorar la decisión en ADR/doc** antes de codificar supuestos.

---

## 10. Continuidad entre productos del ecosistema

Siete Inteligencia Creativa es **una sola capa de inteligencia operacional**: Field, CX, InS, Clever y **Perfil** son **vistas especializadas** sobre contexto compartido:

| Módulo | Enfoque |
|--------|---------|
| **Field** | **PRE-FIELD:** diseño guiado del estudio (brief, instrumento, journey, QA, readiness). **FIELD:** ejecución y supervisión operativa sobre captura externa |
| **InS** | Significado humano (voz, cualitativo) |
| **CX** | Experiencia observada |
| **Clever** | Comunicación ejecutiva (sin sustituir hallazgos oficiales) |
| **Perfil** | Segmentación, comportamiento y continuidad del usuario |

Todos deben **compartir contexto** y eventually **reutilizar patrones** (p. ej. un estudio sectorial que generó riesgos y journey intelligence alimenta recomendaciones futuras en otros módulos). Comparten identidad y la ambición de **memoria metodológica viva** (señales, riesgos, journey, intención del estudio). La implementación es por fases; el **criterio de PR** es unificar memoria, no fragmentarla.

**Ejemplo orientativo:** si en PRE-FIELD se documentan riesgos en un tema delicado (p. ej. onboarding financiero), la arquitectura de producto debe tender a que:

- **FIELD** priorice monitoreo y hallazgos alineados a esos riesgos;
- **CX** sepa qué dimensiones o señales son más relevantes para ese estudio;
- **InS** pueda orientar patrones en materiales cualitativos coherentes con la misma hipótesis;
- **Clever** sintetice narrativa ejecutiva **referenciando** artefactos auditables, sin inventar metodología;
- **Perfil** mantenga continuidad de preferencias y rol del usuario entre productos.

La implementación técnica evoluciona por fases; **la decisión de PR** debe preguntarse si el cambio **acerca** esa continuidad o la fragmenta.

---

## 11. Prioridades técnicas de plataforma (referencia)

Orden **orientativo** para fortalecer el núcleo (validar siempre en código e infra real antes de diseñar contra ellas):

1. Formalizar la capa **intelligence** (`/intelligence` o equivalente) como contrato oficial y **fachada** clara sobre memoria metodológica.
2. **Persistir y versionar** bundles de Study Intelligence como **fuente de verdad** metodológica consumible por FIELD (y horizonte CX/InS/Clever/Perfil).
3. **Redis + Celery** (u orquestación asíncrona equivalente) cuando esté adoptado en despliegue — base para workers especializados.
4. **Workers** para pipelines pesados (transcripción, embeddings, análisis batch, scoring masivo) **desacoplados** del request HTTP principal.
5. **pgvector** y/o **vector store dedicado** (Qdrant, Weaviate, …) para memoria semántica compartida cuando esté adoptado.
6. **Prompt registry** por vertical con versionado y tests; evolución desde el registro central actual hacia árbol `prompt_registry/{field,cx,ins,clever,perfil}/`.
7. **LLM router** multi-proveedor (OpenAI / Anthropic / Gemini / futuros) sin acoplar el negocio a uno solo.
8. **Continuidad explícita** PRE-FIELD ↔ FIELD y exposición gradual a otros consumidores del ecosistema.

**Regla:** no asumir que Redis, workers, embeddings o vectores existen en un entorno sin confirmación explícita del equipo o evidencia en repo/infra.

---

## Metadatos

| Campo | Valor |
|-------|--------|
| Versión | v1.3 (§0–§11 sin cambios de tesis; metadatos: enlace vista arquitectónica por solución [SIETE_SOLUTIONS_ARCHITECTURE_V1.md](SIETE_SOLUTIONS_ARCHITECTURE_V1.md)) |
| Alcance | Dirección de producto y criterio transversal |
| Relación con otros docs | Complementa arquitectura y alcance; [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md); [SIETE_SOLUTIONS_ARCHITECTURE_V1.md](SIETE_SOLUTIONS_ARCHITECTURE_V1.md); [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md) |

---

*Documento vivo: iterar con feedback de diseño y liderazgo de producto; cambios mayores → v2 con changelog breve al inicio.*
