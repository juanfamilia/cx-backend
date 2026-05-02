# 7Field — Arquitectura de experiencia (producto)

**Estado:** activo — **documento maestro simple**: describe *qué debe sentir el usuario* y *qué construimos*. El detalle técnico, fases largas y gobierno profundo siguen en los enlaces al final.

---

## Premisas

1. **7Field no replica** Dooblo, Qualtrics ni ninguna herramienta de captura. **Interpreta ejecución** a partir de datos que el cliente ya tiene en esos sistemas (u otros conectores).
2. **Regla de 3 clics:** desde que el usuario entra con intención de ver campo, hasta tener **una lectura clara de “salud”** del negocio de campo, el flujo feliz no debe forzar más de **tres interacciones principales** (p. ej. login/config → lista/estatus → campaña/proyecto elegido). Todo lo demás es **profundización opcional**, no barrera.
3. **“Salud”** aquí significa: **KPIs acordados** + **scores / riesgo** derivados de reglas versionadas y, cuando aplique, **hallazgos** que explican *por qué* algo está en rojo o ámbar — no una tabla infinita de respuestas crudas.

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

## Implicación para ingeniería y diseño

- **APIs y jobs** deben servir primero ese recorrido: *listado + estatus → detalle de proyecto → KPIs + score + findings*, siempre **multi-tenant** y sin exponer más datos crudos de los necesarios para explicar el semáforo.
- **Nuevas features** se aceptan si **encajan en la jerarquía** “Usuario → empresa → proyecto/campaña → salud (KPI + score + hallazgos)” o si son conectores; se rechazan (o se posponen) si convierten 7Field en **otra pantalla de captura**.
- Los **3 clics** son **criterio de UX y de demo**: si una historia de usuario no puede demostrarse en ese marco, hay que recortar o reproyectar.

### No confundir: lista CRUD vs overview

| URL | Respuesta |
|-----|-----------|
| `GET /api/v1/field/projects?company_id=3` | Lista **plana** de proyectos (solo `FieldProject`: nombre, `client_id`, `status`, `ingest_mode`, fechas…). **No** incluye semáforo ni KPIs. |
| `GET /api/v1/field/projects/overview?company_id=3` | Una **fila enriquecida por proyecto**: `health`, `health_reasons`, `kpis_latest`, hallazgos abiertos por severidad, última corrida de análisis, etc. |
| `GET /api/v1/field/projects/{id}/overview` | **Drill-down** de un proyecto (misma fila + `top_findings`). |

En Swagger / OpenAPI, el overview está en el tag **Siete Field** (no sustituye a `GET /projects`).

---

### Contrato API mínimo (mapeo a 3 clics)

| Clic lógico | Qué hace el usuario | Backend (prefijo típico `/api/v1/field`) |
|-------------|---------------------|-------------------------------------------|
| **1** | Entra y deja listo el conector | `PUT /dooblo/credentials` (u homólogo Qualtrics cuando exista); opcional `GET /dooblo/status`. |
| **2** | Ve **estatus de todos los proyectos** / campañas (semáforo, KPIs ligeros) | `GET /projects/overview` — una sola respuesta agregada por tenant (filtros `company_id` / `client_id` si aplica). |
| **3** | Hace drill-down en **una** campaña / proyecto (“Power BI”) | `GET /projects/{id}/overview` — salud + últimos KPIs + conteos de hallazgos + **muestra corta** de hallazgos abiertos (sin sustituir el listado paginado de `decision-layer/findings` si el usuario profundiza). |

**Profundización** (no cuenta en los 3 clics): sync/análisis (`POST .../sync`, `POST .../decision-layer/...`), KPIs aislados, snapshot operacional, aprobación de hallazgos, export, Clever.

**Scores agregados** (`FieldScore` / fórmula única): cuando existan en modelo, deben colgarse del mismo `GET /projects/{id}/overview` o documentarse aquí en una línea cuando se implemente.

---

## Documentación relacionada (detalle)

- Estrategia y pilares comerciales: [7FIELD_COMMERCIAL_STRATEGY_V1.md](7FIELD_COMMERCIAL_STRATEGY_V1.md)
- Gobierno de hallazgos, criticidad operativa, Clever: [7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md](7FIELD_FINDINGS_GOVERNANCE_AND_EXEC_INTEL_V1.md)
- Contrato mínimo de plataforma: [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md)
- Decisiones estructurales cerradas (motor de reglas, estudios, etc.): [7FIELD_STRUCTURAL_DECISIONS_V1.md](7FIELD_STRUCTURAL_DECISIONS_V1.md)
- Ecosistema e ingest CSV cuando aplique: [ECOSYSTEM_SIETE.md](ECOSYSTEM_SIETE.md) · [FIELD_CSV_2026_1.md](FIELD_CSV_2026_1.md)

---

## Versionado

- **v1–v1.4 (2026‑02‑23 → 2026‑05‑02):** versiones anteriores con mapas de capas, fases A–E, tracción por fase y §9 honestidad repo (archivo histórico en git).
- **v2 (2026‑05‑02):** reescritura **simple**: premisa “no replicar captura”, flujo credenciales → GET empresa → estatus → drill campaña → salud (KPI + score + hallazgos), **regla de 3 clics**; detalle profundo movido a documentos enlazados.
- **v2.1 (2026‑05‑02):** tabla **Contrato API mínimo** (3 clics) + nota scores; alineación con endpoints reales (`/projects/overview`, `/projects/{id}/overview`).
- **v2.2 (2026‑05‑02):** tabla **No confundir** `GET /projects` vs `GET /projects/overview`; Swagger en `list_projects` apunta al overview.
