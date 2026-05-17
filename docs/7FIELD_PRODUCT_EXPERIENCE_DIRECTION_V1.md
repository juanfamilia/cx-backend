# 7Field — Dirección de experiencia de producto (v1)

**Tipo:** criterio transversal (producto, diseño, frontend, backend, IA).  
**Tiempo de lectura:** ~5 minutos.  
**Uso:** citar en PRs y decisiones de alcance; no sustituye especificaciones técnicas detalladas.

---

## 1. Qué es 7Field

7Field es la **capa inteligente sobre la operación de investigación**: conecta **lo que el estudio intenta descubrir** con **lo que realmente ocurre en campo**, de forma continua y auditable.

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

**FIELD debe entender lo que PRE-FIELD intentó lograr**, mediante:

- **Contexto persistente** (no solo “última métrica”).
- **Journey intelligence** y lectura del recorrido esperado vs señales reales.
- **Riesgos esperados** y puntos sensibles acordados en diseño.
- **Sensibilidad metodológica** (tono, carga, orden, advertencias).
- **Lineage y versionado** que permitan confianza enterprise (“qué versión del estudio está viva en campo”).

Sin ese puente, 7Field se siente como **módulos conectados**. Con él, se siente como **un sistema unificado**.

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

### Frontend

- **Shells separados** para PRE-FIELD y FIELD (distinta energía, navegación y copy).
- **Componentes por intención de usuario** (brief, metodología, journey, riesgos, readiness, salud, alertas), no mega-componentes “que lo hacen todo”.
- **Presentation-first**: vistas legibles; contenedores pequeños; estado derivado claro (p. ej. signals/computed).
- **Backend-driven intelligence**: el cliente muestra; no reinterpreta reglas de negocio metodológicas.

### Backend

- **Intelligence-first**: bundles coherentes que alimenten ambos mundos.
- **Source of truth** para señales metodológicas, QA, readiness contextualizado y journey.
- **Persistencia de intención y lineage** para que FIELD compare contra lo diseñado, no contra vacío.

### IA

- **Elevar criterio**, reducir errores, acelerar thinking, sugerir buenas prácticas.
- **Detectar riesgos** y mantener consistencia con lo ya definido.
- **No reemplazar** el rol del investigador ni prometer “cuestionarios mágicos”.

---

## 8. Secuencia de evolución

Orden deliberado para **no rehacer todo sin dirección** ni ensanchar superficie sin núcleo:

1. **Navegación y modelo mental** — Separación clara FIELD → PRE-FIELD / FIELD; shells, lenguaje y ritmo visual distintos.
2. **Pregunta mental → pantalla** — Mapear cada flujo crítico a una pregunta dominante; cortar híbridos.
3. **Convergencia del intelligence bundle** — Un núcleo coherente que alimente preview, riesgos y readiness con la misma historia.
4. **FIELD contextual** — Supervisión que **muestre intención persistida** frente a ejecución (no solo KPIs aislados).

---

## 9. Checklist obligatorio para PRs / features

Antes de aprobar o mergear, la persona revisora debe poder responder **sí** de forma honesta a estas seis preguntas:

1. **¿Este cambio fortalece la continuidad inteligente** (PRE-FIELD ↔ FIELD y, cuando corresponda, el consumo futuro de **memoria metodológica** por CX / InS / Clever / Perfil), o solo añade superficie o datos sueltos?
2. **¿La vista tiene una pregunta mental dominante clara**, o mezcla diseño y operación / varias decisiones a la vez?
3. **¿El texto visible está en lenguaje humano**, sin exponer jerga interna salvo en herramientas explícitas de administración?
4. **¿La inteligencia mostrada viene del backend / bundle coherente**, sin que el frontend “infiera metodología”?
5. **¿Se aplicó progressive disclosure** (lo esencial primero; lo avanzado accesible pero no competitivo)?
6. **¿Evitamos anti-patrones** de la sección 6 (híbrido enterprise, builder mindset, múltiples verdades)?

Si la respuesta honesta es “no” en más de una, **detener o recortar** antes de seguir acumulando complejidad.

---

## 10. Continuidad entre productos del ecosistema

Siete Inteligencia Creativa es **un solo ecosistema**: Field, CX, InS, Clever y **Perfil** comparten identidad, contexto y la ambición de **memoria metodológica viva** (señales, riesgos, journey, intención del estudio).

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

1. Formalizar la capa **intelligence** (`/intelligence` o equivalente) como contrato oficial.
2. **Persistir y versionar** bundles de Study Intelligence como **fuente de verdad** metodológica.
3. **Redis + Celery** (u orquestación asíncrona equivalente) cuando esté adoptado en despliegue.
4. **pgvector** / memoria semántica compartida cuando esté adoptado.
5. **Prompt registry** y gobierno de prompts (coherente con el motor backend).
6. **Continuidad explícita** PRE-FIELD ↔ FIELD y exposición gradual a otros consumidores del ecosistema.

**Regla:** no asumir que Redis, workers, embeddings o vectores existen en un entorno sin confirmación explícita del equipo o evidencia en repo/infra.

---

## Metadatos

| Campo | Valor |
|-------|--------|
| Versión | v1.1 (añadidos §10–§11 continuidad ecosistema y prioridades plataforma) |
| Alcance | Dirección de producto y criterio transversal |
| Relación con otros docs | Complementa arquitectura y alcance; [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md); [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md) |

---

*Documento vivo: iterar con feedback de diseño y liderazgo de producto; cambios mayores → v2 con changelog breve al inicio.*
