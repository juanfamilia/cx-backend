# 7Field — Secuencia de ejecución (Cursor)

**Propósito:** orden **obligatorio** de implementación — prioridad, reglas técnicas, dirección visual y percepción UX. **Operacionaliza** la visión del ecosistema Siete Inteligencia Creativa definida en [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md) y el alcance Field en [7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md](7FIELD_ARCHITECTURE_SCOPE_AND_TRACTION_V1.md).

**Contexto ecosistema:** lo implementado en Field (PRE-FIELD → FIELD, bundles de inteligencia) debe **mantener continuidad** y preparar consumo por otros productos (CX, InS, Clever, Perfil) cuando existan contratos API — sin ensanchar pantallas que contradigan “una pregunta mental por vista” ni duplicar inteligencia que debe vivir en **FastAPI**.

**Regla de trabajo:** ejecutar **en este orden (1 → 9)**. No abrir builders complejos, drag/drop avanzado ni superficie “ERP” antes de cubrir lo que corresponde en cada fase.

---

## 1. Journey Intelligence (primero — prioridad absoluta)

**No** tocar builders complejos todavía.

**Objetivo:** hacer **visible** la inteligencia del recorrido; que PRE-FIELD produzca **contexto vivo** que FIELD consuma sin re-briefing manual.

**Implementar primero:**

- participant journey preview  
- bloques sensibles  
- señales de fatiga  
- abandono esperado  
- riesgos operacionales  
- narrativa del participante  
- prioridades contextuales en FIELD  

**UX:** tarjetas visuales; narrativa humana; recorrido claro; señales automáticas; sensación premium.

**NO:** tablas técnicas en primera clase; schemas visibles; jerga metodológica en superficie; configuraciones infinitas.

**Angular:** componentes visuales pequeños; `signals` / `computed`; evitar lógica pesada en templates; reutilizar primitivas `field-*`.

**IA / datos:** usar datos **reales** de brief / spec / readiness / artefactos persistidos. **No “fake AI”.**

---

## 2. Preview visual elegante del cuestionario

**NO** drag/drop todavía.

**Sí:** preview **inteligente** y **visualmente fuerte**.

**Demo objetivo:** *“entiendo el recorrido del participante en segundos”.*

**Implementar:**

- cards por fase  
- flujo visual (flow)  
- narrativa breve  
- insights contextuales  
- highlights automáticos  
- estructura limpia tipo storytelling  

**Visual:** más whitespace; ritmo vertical; cards grandes; menos tablas; tipografía respirable; progressive disclosure.

---

## 3. Continuidad PRE-FIELD → FIELD

El contexto del estudio debe **viajar automáticamente** (modelo + API + UI).

FIELD debe poder responder **para este estudio**:

- qué importaba en el brief  
- qué riesgos vigilar  
- qué partes son críticas  
- qué hallazgos pesan más  

**NO:** dashboards genéricos desconectados del estudio.

**Criterio por vista en FIELD:** *¿qué significa esto para **este** estudio?*

---

## 4. IA consultiva

La IA debe sentirse **consultiva, metodológica y operacional** — **no** autónoma.

**Implementar:**

- sugerencias cortas  
- riesgos detectados  
- mejoras de redacción  
- warnings de fatiga  
- gaps metodológicos  
- próximos pasos claros  

**UX / microcopy:** lenguaje humano. **Evitar en superficie:** “pipeline”, “schema”, “validator”, “rule package” (eso vive en Detalles técnicos).

---

## 5. UX/UI — simplificación continua

**Regla:** menos densidad en superficie.

**Seguir removiendo:** tablas grandes; bloques largos de texto; etiquetas técnicas; acciones duplicadas; patrones tipo ERP.

**Preferir:** una acción principal; summaries; cards; badges simples cuando aporten; spacing amplio; jerarquía visual clara.

---

## 6. Progressive disclosure

Complejidad técnica **solo** tras “**Detalles técnicos**” (o equivalente).

JSON, lineage, hashes, QA técnico: **siempre** secundarios.

La superficie principal debe sentirse **simple, guiada y premium**.

---

## 7. Angular — arquitectura (disciplina permanente)

**NO:** mega-components; templates gigantes; lógica compleja en HTML.

**SÍ:** smart containers + dumb UI; `computed` / signals; helpers reutilizables; consistencia visual global; **build limpio siempre**.

---

## 8. Python / IA / heurísticas

Python apoya: scoring; heurísticas; QA inteligente; recomendaciones; contextualización; embeddings **cuando** haya valor claro.

**Contrato con la UI:** el **backend analiza** (longitud, fatiga, sesgo, redundancia, orden, consistencia, cobertura metodológica, validaciones, riesgos operacionales); el **frontend solo presenta insights humanos** a partir de API/servicios — no duplicar el motor en Angular salvo formateo trivial.

**Arquitectura del motor:** [7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md](7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md) — paquete `app/study_intelligence/` (`contracts`, `layers.StudyIntelligenceService`, `prompt_registry`); implementación incremental P0→P4.

**No** crear complejidad técnica antes de que exista **valor perceptible** en UI/demo.

Servicios pequeños; outputs auditables; reglas explícitas + IA acotada (alineado al doc maestro).

---

## 9. Regla permanente de producto (priorización)

Cada feature debe generar **al menos una** de estas percepciones:

- “7Field entiende mi estudio”  
- “7Field me ayuda a pensar”  
- “7Field me ayuda a ejecutar”  
- “esto se siente premium”  
- “esto reduce dependencia de seniors”  
- “esto se ve avanzado pero fácil”  

Si **no** genera ninguna con honestidad: **no priorizarla** todavía.

---

## Versionado

- **v1.2 (2026‑05‑16):** §8 — enlace blueprint motor backend (`7FIELD_BACKEND_INTELLIGENCE_ENGINE_V1.md`, `app/study_intelligence/`).
- **v1.1 (2026‑05‑16):** §8 — contrato backend analiza / frontend solo insights humanos (longitud, fatiga, sesgo, redundancia, orden, consistencia, cobertura, validaciones, riesgos operacionales).
- **v1 (2026‑05‑06):** secuencia inicial obligatoria Cursor (Journey Intelligence → preview → continuidad → IA consultiva → UX → disclosure → Angular → Python → regla de percepción).
