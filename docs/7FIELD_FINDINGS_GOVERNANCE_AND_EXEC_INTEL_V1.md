# 7Field — Hallazgos, gobierno operativo y Executive Intelligence (Clever)

**Estado:** activo — **prioridad ejecutiva / producto / arquitectura**.  
**Alcance:** clasificación de criticidad **operativa** (no solo “cómo se ve”), política de decisión (**STOP · FIX_NOW · MONITOR**), scoring con **contexto de negocio**, **versionado de reglas**, condiciones enterprise (logs, Clever, integraciones), y **rol contrato-compatible** de Clever frente al shared contract documentado en [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md).

**No negociable:** el marco de investigación (RIF) vive como **núcleo de 7Field**; sin **shared contract**, no hay ecosistema. Ver constitución en el documento de plataforma.

---

## 1. Principio rector (producto)

**No clasificamos por percepción.** Clasificamos por **costo de ignorar** el hallazgo respecto de:

- validez del estudio o de la decisión de negocio;
- pérdida económica esperada u obligatoriedad contractual;
- reputación o defensa ante cliente/regulador.

Esa es la única métrica de admisión (“¿ROI claro?”) para clasificar evidencia en el motor.

---

## 2. Decisiones cerradas antes de automatizar más

| Decisión | Resolución adoptada |
|----------|---------------------|
| ¿Un mismo estudio puede tener varios Field projects (olas/mercados)? | **Sí.** Un estudio/programa agrupa trabajo; coexisten uno o más proyectos Field bajo política definida por tenant. |
| ¿Quién **sella** diseño/readiness (pre‑field)? | **Roles 0 y 1** pueden sellar artefactos (visibilidad y responsabilidad asumidas por política RBAC; el nombre en UI puede mapearse) salvo **política contractual** que nombre otros aprobadores. |
| ¿Criticidad sólo como severidad UI? | **No.** Obligatorios **criticidad operativa** + **respuesta operativa**, además de severidad/código técnico. |

---

## 3. Dos ejes ortogonales (obligatorio en contrato conceptual)

Todo hallazgo debe poder expresarse con **al menos**:

| Eje | Pregunta | Ejemplos de codificación técnica (ilustrativo) |
|-----|----------|-----------------------------------------------|
| **Severidad de presentación** | ¿Cuánto golpea al tablero? | `critique` / UI / prioridad de visualización (no suficiente sola). |
| **Criticidad operativa** | ¿Ignorarlo puede invalidar el estudio, la decisión o el contrato? | `blocking` vs **informativa** (“mejora” sin frenar ejecución). |
| **Respuesta operativa (única)** | ¿STOP, corregir ya, o sólo vigilar? | Ver §4 — **sin estadillos intermedios que sustituyan decisión.** |

Las listas siguientes refinan **criticidad** con ejemplos; el **tipo técnico** (`code`), la **severidad**, el **score** numérico y la **respuesta obligatoria** deben estar **versionados** y enlazados a reglas aplicadas (§6–7).

---

## 4. Respuesta operativa obligatoria: solo tres valores

Sin “gris ejecutivo”: cada hallazgo debe traducirse a **una sola orden de maniobra**.

| Respuesta interna `operational_gate` | Significado ejecutable |
|---------------------------------------|-------------------------|
| **STOP** | Impide seguir como está: no salida a campo, parada del levantamiento, o cualquier continuación equivalente a **consumir recurso ilegítimo**. Corrección antes de uso o **escalación con bloqueo** explícito. |
| **FIX_NOW** | No bloqueo total pero **prioridad alta**: intervención en ventana cercana antes de producir nuevo daño; **no puede diluirse indefinidamente.** |
| **MONITOR** | **Informativo:** mejora, benchmark, eficiencia, entrenamiento, seguimiento; **sin frenar**. |

Los adjetivos internos pueden mapearse a las dos familias de criticidad así:

| Criticidad operativa (`operational_criticality`) | Tiende a responder con |
|------------------------------------------------|------------------------|
| **Bloqueante** | **STOP**, o —si el diseño del estudio permite contención muy acotada— **FIX_NOW forzado contractualmente**. En la práctica, **STOP** debe ser usual para verdaderamente bloqueantes. |
| **Informativa** | **MONITOR** (usualmente); **FIX_NOW** sólo cuando el proceso de cliente exija “resolver pronto pero sin parar mundo”. |

Implementación debe evitar dashboards **sin vínculo a una de estas tres salidas** y a un **caso decidible**.

---

## 5. Ejemplos de bloqueante vs informativo (orientación de producto)

### 5.1 Pre‑field — típicamente **bloqueante**

Ejemplos (no exhaustivos): cuotas imposibles; filtros rota; mediciones inducidas; doble pregunta crítica en pregunta clave; opciones solapadas con lectura equivocada; scripting incompatible en plataforma objetivo; rutas de navegación erróneas; randomización aplicada donde invalida tratamiento experimental; muestra mal dimensionada donde invalida poder estadístico; target de panel mal definido; criterios de inclusión contradictorios; **instrumento metodológicamente contaminado** que implica incinerar capex de campo si se ejecuta igual.

Si **salir a campo** repetiría un error conocido antes de lanzar, clasificación **STOP** esperada tras validación según política tenant.

### 5.2 Pre‑field — típicamente **informativo**

Optimización sin invalidar estudios ya contratados: longitud alta de cuestionario, wording mejorables, orden subóptimo, fatiga potencial moderada, props de mejoras cualitativas, etc.: **MONITOR**/mejora incremental.

### 5.3 Field — típicamente **bloqueante**

Señales de **fabricación repetida**, coherencias **imposibles** con proceso humano válido (“duración físicamente incompatible”, GPS sistémico falso, duplicidades operativamente intolerables donde el contrato exige unicidad absoluta por target, supervisors con patrones de evidencia objetiva fraudulenta cuando la política marca fraude probado**, etc.

Regla práctica Field: si **los siguientes datos** producidos estarían irrevocablemente contaminados antes de nueva intervención, **STOP** o proceso de aislamiento con **bloqueio de entrada** igual.

### 5.4 Field — típicamente **informativo**

**MONITOR**/mejora: performance leve fuera benchmark, zonas menos productivas, desviaciones de duración leves dentro de política contractual, rutas mejorables sin indicio de ilegitimidad estadística sistemática.

Estas categorías enlazan con Severidad (**§6**) mediante **mapping versionado**.

---

## 6. Dimensiones obligatorias de scoring (contrato ejecutable)

Cada hallazgo que participe del motor de decisión debe ser capaz de poblar dimensiones objetivas (**no bastan adjetivos**):

| Dimensión | Rol |
|-----------|-----|
| `severity`/`severity_model_version` | Cómo se muestra/comunica dentro de thresholds de producto |
| **`estimated_financial_impact`** | Rango orden de magnitud o banda acordado con método documentado (**no** “invent”; estimación modelo + supuestos) |
| **`harm_probability`** | Probabilidad de materialización del daño condicionado a ignorar hasta ventana siguiente |
| **`operational_urgency`** | Ventanas de SLA operativo exigibles (**FIX_NOW** vs backlog) |
| **`ownership`** | Rol / usuario responsable inicial (con override según proceso) |

**Regla técnica:** las evaluaciones de **risk score**, **clasificación en bands** y **gates automáticas** están **firmadas por** **`scoring_version_id` + política efectiva fecha** (**§7**).

---

## 7. Versionado y gobierno — reglas de scoring como activo

### 7.1 Qué se versiona (sin excepción si afecta resultado)

Todo lo siguiente es **contrato**:

- Umbrales y reglas **deterministas** (GPS, tiempo mínimo, straight lining threshold, thresholds de quotas, duplicidades, etc.)
- Pesos dentro de combinaciones donde el score **no es trivialemente estable**
- Rangos donde la severidad o la bandera **STOP/FIX_NOW/MONITOR**
- Cambios políticos automatizados (si existen disparadores, deben ser **reglas igualmente revisionadas**)
- Policies de clasificación incluso donde participa IA (**prompt + parámetro + modelo + condición para validación humana**)

### 7.2 Qué guarda cada versión (audit trail mínimo)

Registro debe permitir responder en disputa contractual:

- nombre de regla, descripción funcional
- valores **antes/después** (literales donde aplique hash de payload complejo)
- **motivo** del cambio, impacto esperado declarado por la parte de negocio
- **fecha efectiva** aplicada desde entorno servidor
- aprobadores (Producto/Governance L1+L2+L3 donde aplique, ver §7.3)
- **tenant scope**: global empresa / proyecto / cliente contratado donde exista override
- opcional plan de rollback ejecutable

Sin esto → **sin venta regulated enterprise defendible**.

### 7.3 Niveles de gobierno (no negociables)

| Nivel | Responsabilidad | Roles típicos | No debe hacer solo |
|------|-----------------|---------------|---------------------|
| **Governance Negocio (L1)** | Define *qué* debe cambiar (riesgo método/negocio). | Product Owner, director research, método. | Implementar solo sin L2. |
| **Governance técnico (L2)** | Valida seguridad, impacto técnico, compatibilidad, rollback. | CTO, lead backend, arquitectura. | Cambiar criterios de negocio sin L1. |
| **Aprobaciones sensibles (L3)** | Clientes regulados o estudios donde el contrato exige firma cliente/dirección. | Dirección, sponsor cliente si aplica. | Sustituir veto regulatorio donde aplique ley/contrato. |

Sin hardcode secreto umbrales: **solo** mediante **motor de configuración revisado.**

### 7.4 Comparabilidad temporal

Toda reevaluación **persistible** lleva **`scoring_version_id` junto score final** donde el resultado es **comparable en el tiempo** (benchmarking internos/externos donde contrato permite).

Dos valores numéricos iguales con **`scoring_version_id` distinto** deben poder **distinguirse** en export y en auditoría (“mismo número, **distinta política efectiva**”).

---

## 8. Comparabilidad, rollback y parametrización

- **Rollback** no es opcional donde exista materialidad regulatoria o contractual alta.
- Preferencia arquitectónica: `rule_sets` / `rule_versions` como **almacenes inmutables** de versiones efectivas aplicadas.
- Overrides por tenant solo si están **gobernadas** con el mismo rigor que reglas globales.

---

## 9. Logs, Clever, integraciones y export — barrera enterprise

### 9.1 Retención y export regulatorio-ready

Los eventos mínimos a auditar donde clientes grandes:

- seguridad (**login**, cambios permiso)
- data provenance uploads y reprocesamiento
- generación/evolución de hallazgos y decisiones (incluye overrides manuales)
- ejecuciones de jobs automatizadas y generación de hallazgos
- consumo de Clever **sobre datos sensibles** (registro de consumo, no sólo error técnico)

**Retención** configurable **por tenant** (12/24/36 meses u obligación contractual).

**Export** productizados: CSV/JSON (máquina), Excel humano, PDF ejecutivo cuando narrativa final lo requiera.

### 9.2 Límites de Clever (inputs)

**Sí:** hallazgos ya generados y gobernados, resúmenes permitidos, metadatos no sensibles, transcripciones **autorizadas**, contexto agregado no PII salvo contrato.

**No:** credenciales, PII contrato-prohibida, **reglas críticas sin governance**, scoring bruto sin contexto de versión, prompts **no auditables**, cross-tenant, **decisiones irreversibles basadas solo en Clever**.

**Frase rectora:** Clever **interpreta y resume**; **no decide** lo que implica **STOP** legal o contractual sin trazabilidad humana explícita contractualmente permitida.

### 9.3 Mapa de integraciones (honestidad comercial)

| Fase | Integración | Postura |
|------|-------------|---------|
| Hoy (debe venderse real) | SurveyToGo/Dooblo-style API, CSV, Excel estructurado, upload controlado, metadatos | **Soportado** |
| Roadmap cercano | Qualtrics, QuestionPro, SurveyCTO, APIs REST standard, CRM/ERP básico | **Roadmap acotado** — no “disponible ya” |
| Premium / largo plazo | SAP/Salesforce/Oracle CX, connectors DWH tiempo real/streaming tipo Power BI | **No comprometer fecha** públicamente |

---

## 10. Rol producto Clever como Executive Intelligence (no sólo summaries)

Clever debe tender a producir **claridad decisoria**, métricas accionando **decisión**, dentro de formato que permita usar en **junta ejecutiva**:

**Salidas orientadas (no páginas):**

| Salida esperada |
|-----------------|
| **Executive storyline** narrative (una frase ejecutiva causal con evidencia trasera) |
| Priorización ejecutiva verdaderamente ordenada (**no urgencia simulada**) |
| Recomendaciones con **verbos operativos** (detener, corregir, reentrenar, auditar, revalidar…) |
| **Impacto económico** cuando modelo lo permita (con supuestos y disclaimers reproducibles) |
| **Documento ejecutivo-ready** donde contrato así lo establezca |

**Framework narrativo típico** (no slide filler): Contexto→Evidencia→Riesgo de inacción→Decisión solicitada→Impacto económico/reputacional declarativo→ siguiente ownership.

**No KPI “número de slides generadas”.** KPIs producto: tiempo a decisión, reducción rework, confianza medida cliente, renovación donde contrato permite medir correlación causal.

Clever potencia velocidad ejecutiva pero **requiere entrada gobernada** y **produce salidas auditadas** igual que hallazgos.

---

## 11. Extensiones al shared contract mínimo

Además de los campos definidos en SIETE, los hallazgos Field deben poder transportar (schema evolutivo versionado):

| Campo conceptual | Descripción |
|--------------------|-------------|
| `company_id`, `owner_user_id` | tenant + accountability |
| **`operational_criticality`** | blocking / informative (u sinónimos localizados) |
| **`operational_gate`** | STOP \| FIX_NOW \| MONITOR |
| `finding_code`, `severity`, **`scoring_dimensions`** (impacto probabilidad urgencia…) | |
| **`rule_pack_id`** + **`scoring_version_id`** | qué combinación contractual generó clasificación exacta |
| `decision_audit_log_refs` | historial approvals |
| vínculos a `study` / `study_version`, `field_project`, entidades operativa (survey_id, interviewer_id,…) | traceability lattice |

Todos los sistemas deben poder participar según permisos (**Field / InS / CX / Clever**) sin duplicar un esquema de hallazgos incompatible entre módulos.

---

## 12. No construir así (lista explícita)

- Parametrización silenciosa en producción sin versionado.
- “IA de método” donde basten reglas deterministas reproducibles.
- Dashboards sin acción ejecutable asociada.
- Segundo modelo de hallazgos paralelo que no sea **interoperable** con el mismo contrato de API.

---

## 13. Decisiones antes de primera migración del modelo extendido

Ya contestadas §2. Restantes para el arranque de ingeniería:

1. Estructuras JSON inicial para **`scoring_dimensions`** y mapping **STOP / FIX_NOW / MONITOR**.
2. Almacenamiento de `rule_versions`: tablas físicas frente a blobs inmutables (trade-off explícito).
3. ¿Override por `field_project`, `study` o cliente final (`end_client`) primero?

---

## 14. Versionado de este documento

- **2026‑02‑23 — v1.0:** taxonomías operativas, tri‑estado de respuesta ejecutable, gobierno de versiones de scoring, límites de Clever, integraciones y Executive Intelligence alineados al contrato de plataforma.

---

Referencias cruzadas: [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md) · [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md).
