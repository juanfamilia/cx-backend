# Field — formato CSV `2026.1` (piloto)

Primera versión orientada a **torre de control** (avance y calidad), no a microdatos de cuestionario. Forma parte del producto **Field** dentro del **ecosistema Siete Inteligencia Creativa**; criterios transversales de experiencia y continuidad entre productos: [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md).

## Columnas obligatorias

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `case_id` | string | Identificador único de caso en el levantamiento. |
| `wave_id` | string | Oleada o versión de campo (libre, estable por estudio). |
| `interviewer_id` | string | Quién ejecutó el caso. |
| `disposition` | string | Estado final (ej. `completed`, `refused`, `partial`). |
| `started_at` | ISO 8601 | Inicio. |
| `completed_at` | ISO 8601 o vacío | Fin (vacío si parcial). |
| `duration_sec` | int | Duración en segundos (puede derivarse en ETL). |

## Opcionales

| Columna | Descripción |
|---------|-------------|
| `quota_cell` | Celda de cuota (string). |
| `lat`, `lon` | Coordenadas si aplica política y consentimiento. |
| `flags` | Lista separada por `;` de flags del conector (ej. `duration_low`). |

## Próximo paso técnico

Endpoint `POST /field/projects/{id}/import` que valide cabeceras, cree `field_import_runs` y persista filas en staging (tabla `field_import_rows` o schema dedicado).
