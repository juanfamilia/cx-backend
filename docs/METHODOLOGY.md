# Metodología de Evaluación de Calidad de Servicio

> Documento oficial del modelo de calidad de servicio (Service Quality Framework)
> integrado en la plataforma. Esta metodología es **híbrida**: no pretende ser
> investigación propia, sino una **orquestación operativa** de marcos reconocidos
> internacionalmente, adaptada al contexto LATAM y a la industria de cada cliente.
>
> **Ecosistema Siete:** este framework alimenta la dimensión CX / evaluación dentro de la plataforma unificada; criterios transversales de producto y continuidad entre módulos en [SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md](SIETE_PLATFORM_MINIMUM_CONTRACT_V1.md) y [7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md](7FIELD_PRODUCT_EXPERIENCE_DIRECTION_V1.md).

---

## 1. Filosofía

La calidad del servicio al cliente es un constructo multidimensional que ha sido
estudiado durante más de cuatro décadas. En lugar de proponer un modelo cerrado
y propietario, la plataforma integra los marcos más citados de la disciplina y
los traduce en **competencias observables** que pueden ser medidas tanto por
auditores humanos como por modelos de inteligencia artificial.

Cada competencia del modelo operativo está anclada al menos a una **dimensión**
de un marco reconocido, con su respectiva referencia bibliográfica. Esto
garantiza:

1. **Trazabilidad**: cada score tiene un linaje académico o normativo.
2. **Defensibilidad**: los resultados son auditables frente a terceros.
3. **Interoperabilidad**: las métricas pueden compararse con estudios del sector.
4. **Adaptabilidad**: se personaliza por industria y empresa sin perder la base
   común.

---

## 2. Marcos de referencia integrados

### 2.1 SERVQUAL

**Autores**: Parasuraman, A., Zeithaml, V. A., & Berry, L. L.

**Referencia**: Parasuraman, A., Zeithaml, V. A., & Berry, L. L. (1988).
SERVQUAL: A multiple-item scale for measuring consumer perceptions of service
quality. *Journal of Retailing*, 64(1), 12–40.

**Qué aporta**: Cinco dimensiones base para medir calidad percibida del
servicio:

- **Tangibles**: apariencia de instalaciones, equipos, personal y materiales.
- **Confiabilidad (Reliability)**: capacidad de realizar el servicio prometido
  de forma precisa y consistente.
- **Capacidad de Respuesta (Responsiveness)**: disposición para ayudar al
  cliente y proveer servicio oportuno.
- **Seguridad (Assurance)**: conocimiento, cortesía y capacidad de los
  empleados para inspirar confianza.
- **Empatía (Empathy)**: atención individualizada y cuidado al cliente.

**Uso en la plataforma**: marco base para clasificar competencias cualitativas
de interacción agente-cliente. Cada competencia puede pertenecer a una o más
de las cinco dimensiones.

### 2.2 RATER (simplificación operativa de SERVQUAL)

**Autores**: Berry, L. L., Parasuraman, A., & Zeithaml, V. A.

**Referencia**: Berry, L. L., Parasuraman, A., & Zeithaml, V. A. (1991).
*Marketing Services: Competing through Quality*. The Free Press.

**Qué aporta**: Nemotecnia operativa (R-A-T-E-R) para las mismas cinco
dimensiones de SERVQUAL, pensada para capacitación de equipos de front-office.

### 2.3 NPS — Net Promoter Score

**Autor**: Reichheld, F. F.

**Referencia**: Reichheld, F. F. (2003). The one number you need to grow.
*Harvard Business Review*, 81(12), 46–55.

**Qué aporta**: Indicador de lealtad del cliente (escala 0–10) con tres
segmentos: Detractores (0–6), Pasivos (7–8), Promotores (9–10).
NPS = %Promotores − %Detractores.

**Uso en la plataforma**: el modelo infiere un NPS probable de cada
interacción (`nps_inferred`) a partir de sentimiento, resolución y esfuerzo
del cliente. No sustituye a una encuesta NPS real, pero permite proyecciones
tempranas y correlaciones con el comportamiento operativo.

### 2.4 CES — Customer Effort Score

**Autores**: Dixon, M., Freeman, K., & Toman, N.

**Referencia**: Dixon, M., Freeman, K., & Toman, N. (2010). Stop trying to
delight your customers. *Harvard Business Review*, 88(7/8), 116–122.

**Qué aporta**: Métrica que mide el esfuerzo que debe hacer un cliente para
resolver su necesidad. Demuestra que reducir el esfuerzo correlaciona más con
lealtad que “superar expectativas”.

**Uso en la plataforma**: CES se calcula determinísticamente a partir de
señales observables (repreguntas, tiempos de espera, escalamientos,
abandono).

### 2.5 Forrester CX Index

**Fuente**: Forrester Research, Inc.

**Referencia**: Forrester Research. (2016). *The Forrester Customer Experience
Index methodology*. Forrester Research, Inc. (ver reportes anuales del
CX Index).

**Qué aporta**: Tres pilares para evaluar experiencia del cliente:

- **Efectividad (Effectiveness)**: el servicio entrega valor al cliente.
- **Facilidad (Ease)**: el cliente obtiene el valor con el menor esfuerzo.
- **Emoción (Emotion)**: el cliente se siente bien durante y después.

**Uso en la plataforma**: pilar transversal para reportes ejecutivos. Cada
evaluación se ubica en un heatmap Efectividad × Facilidad × Emoción.

### 2.6 ISO 10002:2018 — Gestión de quejas y reclamaciones

**Fuente**: International Organization for Standardization.

**Referencia**: ISO 10002:2018. *Quality management — Customer satisfaction —
Guidelines for complaints handling in organizations*. ISO, Geneva.

**Qué aporta**: Principios para el tratamiento de quejas: visibilidad,
accesibilidad, capacidad de respuesta, objetividad, confidencialidad,
enfoque al cliente, responsabilidad, mejora.

**Uso en la plataforma**: criterios de compliance para competencias de manejo
de reclamos y escalamientos.

### 2.7 ISO 18295 — Centros de contacto con clientes

**Fuente**: International Organization for Standardization.

**Referencias**:

- ISO 18295-1:2017. *Customer contact centres — Part 1: Requirements for
  customer contact centres*. ISO, Geneva.
- ISO 18295-2:2017. *Customer contact centres — Part 2: Requirements for
  clients using the services of customer contact centres*. ISO, Geneva.

**Qué aporta**: Requisitos estructurados para la operación de centros de
contacto, incluyendo competencias del personal, protocolos de atención,
medición y mejora continua.

**Uso en la plataforma**: columna vertebral de las competencias operativas
del journey (apertura, identificación, escucha, manejo, cierre).

### 2.8 COPC CX Standard

**Fuente**: COPC Inc.

**Referencia**: COPC Inc. (2022). *COPC Customer Experience (CX) Standard,
release 6.2*. COPC Inc.

**Qué aporta**: Estándar operativo global para centros de contacto y
experiencia de cliente, con KPIs de eficiencia, calidad y satisfacción.

**Uso en la plataforma**: referencia para definiciones de indicadores
operativos (AHT, FCR, abandono, CSAT, etc.) cuando la empresa los reporta.

### 2.9 Modelo Kano

**Autor**: Kano, N.

**Referencia**: Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984).
Attractive quality and must-be quality. *Journal of the Japanese Society for
Quality Control*, 14(2), 39–48.

**Qué aporta**: Clasificación de atributos del servicio en:

- **Básicos (Must-be)**: se dan por sentado; su ausencia causa insatisfacción.
- **De desempeño (One-dimensional)**: más es mejor; relación lineal con
  satisfacción.
- **Atractivos (Delighters)**: sorprenden positivamente.

**Uso en la plataforma**: clasifica cada competencia para entender qué
genera deserción (básicos no cumplidos) vs. qué genera lealtad
(atractivos).

### 2.10 Service Recovery Paradox

**Autores**: Hart, C. W. L., Heskett, J. L., & Sasser, W. E., Jr.

**Referencia**: Hart, C. W. L., Heskett, J. L., & Sasser, W. E., Jr. (1990).
The profitable art of service recovery. *Harvard Business Review*, 68(4),
148–156.

**Qué aporta**: Evidencia de que una recuperación de servicio excepcional
puede generar mayor lealtad que una interacción perfecta sin incidentes.

**Uso en la plataforma**: marco para competencias de manejo de
incidencias, quejas y escalamiento.

### 2.11 Moments of Truth

**Autor**: Carlzon, J.

**Referencia**: Carlzon, J. (1987). *Moments of Truth: New Strategies for
Today’s Customer-Driven Economy*. Ballinger Publishing.

**Qué aporta**: Concepto de que cada punto de contacto entre empresa y
cliente es un “momento de verdad” que define la percepción de marca.

**Uso en la plataforma**: base conceptual para la segmentación por fases
(`interaction_phases`: ENTRY, ATTENTION, CLOSURE, WAITING, ESCALATION)
del análisis IA.

---

## 3. Jerarquía del modelo operativo

```
Framework (SERVQUAL, NPS, CES, Forrester, ISO, COPC, Kano, ...)
   └─ FrameworkDimension (SERVQUAL.Empathy, Forrester.Emotion, ...)
        ↑
        │ (referenciada por)
        │
   QualityCompetency (GREETING_STANDARD, ACTIVE_LISTENING, ...)
        ├─ CompetencyIndicator (positivos / negativos, observables)
        └─ measurement_type (boolean / likert / number)

Industry (BANCA, RETAIL, SALUD, ...)
   └─ IndustryTemplate (competencias sugeridas + peso por industria)

Company
   ├─ industry_id
   └─ CompanyCompetencyConfig (activación y peso custom por empresa)

SurveyAspect
   └─ competency_id (enlaza el ítem del formulario con la competencia)
```

### 3.1 Capas de personalización

1. **Global** (mantenido por superadmin): catálogo de `frameworks`,
   `framework_dimensions` y `quality_competencies`.
2. **Industria** (mantenido por superadmin): `industry_templates` define qué
   competencias aplican, su peso sugerido y cuáles son obligatorias para una
   industria.
3. **Empresa** (admin de empresa): `company_competency_configs` permite
   activar/desactivar competencias del template y ajustar pesos dentro de
   rangos permitidos.
4. **Formulario**: cada `SurveyAspect` puede enlazarse a una
   `quality_competency`, de modo que el Gap Analysis humano-IA use la
   competencia explícita en lugar de heurísticas de palabras clave.

---

## 4. Industrias soportadas (seeder inicial)

| Código | Industria | Frameworks prioritarios |
|---|---|---|
| `BANCA` | Banca y servicios financieros | SERVQUAL, ISO 18295, COPC |
| `RETAIL` | Retail y consumo masivo | SERVQUAL, Kano, Moments of Truth |
| `SALUD` | Salud y servicios médicos | SERVQUAL, ISO 18295, ISO 10002 |
| `TELCO` | Telecomunicaciones | CES, COPC, Service Recovery |
| `HORECA` | Hotelería, restaurantes y turismo | SERVQUAL, Kano, Moments of Truth |
| `SEGUROS` | Seguros | SERVQUAL, ISO 10002, Service Recovery |
| `EDUCACION` | Educación | SERVQUAL, Kano |
| `GOBIERNO` | Sector público y servicios ciudadanos | ISO 10002, CES |
| `LOGISTICA` | Logística, transporte y última milla | CES, COPC, Service Recovery |
| `TURISMO` | Turismo y experiencias | SERVQUAL, Kano, Moments of Truth |

---

## 5. Competencias base (catálogo inicial)

El seeder inicial provee aproximadamente 25 competencias agrupadas por
categoría de la interacción. Cada una cita al menos una dimensión de un
marco reconocido:

### 5.1 Apertura (OPENING)

- `GREETING_STANDARD` — Saludo y bienvenida protocolar
  (SERVQUAL.Responsiveness + ISO 18295).
- `AGENT_IDENTIFICATION` — Identificación del colaborador por nombre
  (SERVQUAL.Assurance + ISO 18295).
- `COMPANY_BRANDING` — Mención de la empresa/marca
  (ISO 18295).

### 5.2 Atención y Gestión (ATTENTION)

- `ACTIVE_LISTENING` — Escucha activa sin interrumpir
  (SERVQUAL.Empathy).
- `NEED_IDENTIFICATION` — Identificación correcta de la necesidad del cliente
  (SERVQUAL.Reliability + Forrester.Effectiveness).
- `CLEAR_COMMUNICATION` — Claridad y precisión en la información entregada
  (SERVQUAL.Reliability + Forrester.Ease).
- `EMPATHY_DEMONSTRATION` — Demostración explícita de empatía
  (SERVQUAL.Empathy + Forrester.Emotion).
- `PROFESSIONAL_TONE` — Tono y vocabulario profesional
  (SERVQUAL.Assurance).
- `KNOWLEDGE_ACCURACY` — Conocimiento técnico/producto correcto
  (SERVQUAL.Assurance).

### 5.3 Resolución (RESOLUTION)

- `PROBLEM_RESOLUTION` — Resolución efectiva del problema o necesidad
  (SERVQUAL.Reliability + Forrester.Effectiveness).
- `FIRST_CONTACT_RESOLUTION` — Resolución en el primer contacto
  (COPC CX.FCR).
- `ALTERNATIVE_OFFERING` — Ofrecimiento de alternativas cuando no hay
  solución inmediata (Service Recovery).
- `ESCALATION_HANDLING` — Escalamiento ordenado cuando corresponde
  (ISO 10002).

### 5.4 Valor Agregado (VALUE)

- `PRODUCT_OFFERING` — Ofrecimiento proactivo de productos/servicios
  relevantes (Kano.Attractive).
- `CROSS_SELL` — Venta cruzada pertinente (Kano.Attractive).
- `PROACTIVE_INFORMATION` — Información proactiva no solicitada pero útil
  (Kano.Attractive + Forrester.Emotion).

### 5.5 Esfuerzo del cliente (EFFORT)

- `LOW_EFFORT_INTERACTION` — Cliente logra su objetivo con bajo esfuerzo
  (CES + Forrester.Ease).
- `NO_REPETITION` — Cliente no debe repetir información ya dada
  (CES + COPC CX).
- `REASONABLE_WAIT_TIME` — Tiempos de espera razonables
  (ISO 18295 + COPC CX).

### 5.6 Cierre (CLOSURE)

- `CLOSURE_STANDARD` — Cierre protocolar (confirmación, agradecimiento,
  despedida) (ISO 18295).
- `CONFIRMATION_OF_RESOLUTION` — Confirmación de que la necesidad fue
  satisfecha (Forrester.Effectiveness).
- `NEXT_STEPS_COMMUNICATION` — Comunicación clara de próximos pasos
  (SERVQUAL.Reliability).

### 5.7 Compliance y Emocional (COMPLIANCE_EMOTIONAL)

- `CUSTOMER_EMOTION_TRACKING` — Registro del estado emocional del cliente
  (Forrester.Emotion + Moments of Truth).
- `COMPLAINT_HANDLING` — Manejo adecuado de quejas
  (ISO 10002 + Service Recovery).
- `DATA_PRIVACY_COMPLIANCE` — Cumplimiento de privacidad de datos
  (SERVQUAL.Assurance + ISO 18295).

---

## 6. Operacionalización en la plataforma

1. El superadmin mantiene el catálogo global (industrias, frameworks,
   competencias, indicadores) a través de endpoints dedicados.
2. Al crear o editar una empresa, el superadmin asigna una industria. El
   sistema precarga el template correspondiente como configuración inicial.
3. El administrador de la empresa puede activar/desactivar competencias y
   ajustar pesos dentro de los límites permitidos por la industria.
4. Al construir un formulario de evaluación (`SurveyForm`), el sistema
   sugiere aspectos a partir de las competencias activas de la empresa. Cada
   aspecto queda vinculado a su competencia mediante `competency_id`.
5. El prompt del modelo de IA se construye dinámicamente con las definiciones
   e indicadores de las competencias activas. Esto elimina la subjetividad
   del analista LLM y produce resultados consistentes entre campañas.
6. El Gap Analysis compara la respuesta del auditor humano con la evaluación
   de la IA usando la competencia explícita, no heurísticas de palabras clave.
7. Los reportes ejecutivos presentan resultados agregados por dimensión de
   marco (por ejemplo: *SERVQUAL.Empathy = 4.2/5 vs. promedio industria
   banca = 4.0*), permitiendo benchmarking interpretable.

---

## 7. Gobernanza del modelo

- Las actualizaciones al catálogo global quedan registradas en `audit_logs`.
- Las versiones del template por industria se versionan (no se sobrescriben)
  para que las evaluaciones históricas conserven la definición vigente al
  momento de su creación.
- Los cambios de configuración por empresa son auditables y requieren
  justificación cuando afectan competencias marcadas como obligatorias por
  la industria.

---

## 8. Referencias completas (APA 7)

- Berry, L. L., Parasuraman, A., & Zeithaml, V. A. (1991). *Marketing
  Services: Competing through Quality*. The Free Press.
- Carlzon, J. (1987). *Moments of Truth: New Strategies for Today’s
  Customer-Driven Economy*. Ballinger Publishing.
- COPC Inc. (2022). *COPC Customer Experience (CX) Standard, release 6.2*.
  COPC Inc.
- Dixon, M., Freeman, K., & Toman, N. (2010). Stop trying to delight your
  customers. *Harvard Business Review*, 88(7/8), 116–122.
- Forrester Research. (2016). *The Forrester Customer Experience Index
  methodology*. Forrester Research, Inc.
- Hart, C. W. L., Heskett, J. L., & Sasser, W. E., Jr. (1990). The
  profitable art of service recovery. *Harvard Business Review*, 68(4),
  148–156.
- International Organization for Standardization. (2017). *ISO 18295-1:
  Customer contact centres — Part 1: Requirements for customer contact
  centres*. ISO.
- International Organization for Standardization. (2017). *ISO 18295-2:
  Customer contact centres — Part 2: Requirements for clients using the
  services of customer contact centres*. ISO.
- International Organization for Standardization. (2018). *ISO 10002:
  Quality management — Customer satisfaction — Guidelines for complaints
  handling in organizations*. ISO.
- Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984). Attractive
  quality and must-be quality. *Journal of the Japanese Society for
  Quality Control*, 14(2), 39–48.
- Parasuraman, A., Zeithaml, V. A., & Berry, L. L. (1988). SERVQUAL: A
  multiple-item scale for measuring consumer perceptions of service quality.
  *Journal of Retailing*, 64(1), 12–40.
- Reichheld, F. F. (2003). The one number you need to grow. *Harvard
  Business Review*, 81(12), 46–55.
