# SIETE CX - PROMPT REFERENCE DOCUMENTATION

**Version:** 1.0  
**Last Updated:** January 2025  
**Purpose:** Guide for creating and managing AI prompts in Siete CX

---

## TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [Prompt Types](#2-prompt-types)
3. [Default Dual-Analysis Prompt](#3-default-dual-analysis-prompt)
4. [Creating Custom Prompts](#4-creating-custom-prompts)
5. [Best Practices](#5-best-practices)
6. [Industry-Specific Examples](#6-industry-specific-examples)
7. [Prompt Testing & Validation](#7-prompt-testing--validation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. OVERVIEW

### 1.1 What is Prompt Manager?

The **Prompt Manager** system allows companies to customize AI analysis prompts for their specific industry, brand guidelines, and evaluation criteria. Instead of using a one-size-fits-all approach, each company can create prompts tailored to:

- Industry standards (banking, retail, healthcare, hospitality)
- Brand voice and values
- Specific KPIs and metrics
- Regional or cultural considerations
- Custom evaluation frameworks

### 1.2 How It Works

```
1. Admin creates custom prompt via API
   └─> POST /api/v1/prompts

2. Prompt stored in database (prompt_managers table)
   └─> Linked to company_id

3. Shopper submits evaluation with video
   └─> POST /api/v1/evaluations

4. Background AI analysis triggered
   └─> System checks for active company prompt
   └─> Uses custom prompt if exists, otherwise default

5. GPT-4o analyzes transcription
   └─> Generates Vista Ejecutiva + Vista Operativa

6. Results stored in evaluation_analysis table
```

### 1.3 Prompt Architecture

Each prompt consists of:

- **Company ID**: Links prompt to specific company
- **Prompt Name**: Descriptive identifier
- **Prompt Type**: `dual_analysis`, `executive_only`, `operative_only`, `custom`
- **System Prompt**: Full prompt text for GPT-4o
- **Is Active**: Boolean (only one prompt per type can be active)
- **Metadata**: JSON for additional config (temperature, max_tokens, etc.)

---

## 2. PROMPT TYPES

### 2.1 Dual Analysis (Default)

**Type:** `dual_analysis`

**Output:** Executive narrative + JSON operative data

**Use Case:** Comprehensive analysis for most industries

**Example Use:**
- Banking mystery shopping
- Retail customer experience
- Call center quality assurance
- Hospitality service evaluation

---

### 2.2 Executive Only

**Type:** `executive_only`

**Output:** Narrative analysis only (no JSON)

**Use Case:** When human-readable insights are sufficient

**Example Use:**
- Board-level summaries
- Client presentations
- Training material creation

---

### 2.3 Operative Only

**Type:** `operative_only`

**Output:** JSON structured data only

**Use Case:** Feeding dashboards, data pipelines, ML models

**Example Use:**
- Real-time dashboard updates
- Automated alerting systems
- Trend analysis algorithms

---

### 2.4 Custom

**Type:** `custom`

**Output:** Fully custom format

**Use Case:** Specialized evaluation needs

**Example Use:**
- Compliance auditing
- Technical support quality
- Multi-language analysis

---

## 3. DEFAULT DUAL-ANALYSIS PROMPT

### 3.1 Prompt Structure

The default prompt used when no custom prompt exists:

```
role: >
Eres un analista dual de Customer Experience (CX) con enfoque consultivo y metodológico. 
Debes entregar un análisis balanceado entre storytelling ejecutivo y consistencia cuantitativa.  
Tu trabajo debe alinearse con las mejores prácticas de la disciplina (Forrester CX Index, 
NPS de Bain & Company, Customer Effort Score de Gartner, estándares de CXPA y Harvard Business Review).

contexto: >
Recibirás una transcripción de interacción entre cliente y agente (real o mystery shopper).  
Tu misión es producir dos vistas:  
1) *Vista Ejecutiva Consultiva* para directivos (narrativa, insights, emociones, acciones).  
2) *Vista Operativa Metodológica* en formato JSON rígido (KPIs, verbatims, acciones automáticas).
```

### 3.2 Executive View Components

1. **🧾 Resumen ejecutivo** (3 líneas máx.)
2. **🧠 Mini transcripción clave** (2-3 frases textuales)
3. **📌 Temas principales tratados**
4. **😐 Tono emocional** cliente y agente
5. **👥 Identificación de roles**
6. **📊 Evaluación cuantitativa** (1-5):
   - Saludo y bienvenida
   - Escucha activa
   - Claridad en la información
   - Resolución del problema
   - Empatía
   - Cierre de conversación
   - Profesionalismo general
7. **✅ Buenas prácticas observadas**
8. **⚠ Oportunidades de mejora** (operativas y emocionales)
9. **🚀 Oportunidades de entrenamiento**
10. **🔥 Frases críticas detectadas**
11. **💬 Recomendaciones accionables** (alta/media/baja prioridad)
12. **📈 NPS inferido** (0-10, con justificación)
13. **🧩 Impacto estimado en el negocio**

### 3.3 Operative View JSON Schema

```json
{
  "id_entrevista": "string",
  "timestamp_analisis": "YYYY-MM-DD HH:MM:SS",
  "metadata": {
    "canal": "callcenter/whatsapp/presencial",
    "duracion_segundos": 0,
    "pais": "string",
    "sucursal_id": "string",
    "segmento_cliente": "string"
  },
  "IOC": {
    "score": 0-100,
    "justificacion": "Texto breve"
  },
  "IRD": {
    "score": 0-100,
    "justificacion": "Texto breve"
  },
  "CES": {
    "score": 0-100,
    "justificacion": "Texto breve"
  },
  "Calidad": {
    "saludo": boolean,
    "identificacion": boolean,
    "ofrecimiento": boolean,
    "cierre": boolean,
    "valor_agregado": boolean
  },
  "Verbatims": {
    "positivos": ["frase (origen, timestamp)"],
    "negativos": ["frase (origen, timestamp)"],
    "criticos": ["frase (origen, timestamp)"]
  },
  "acciones_sugeridas": ["acción automática basada en KPIs"]
}
```

### 3.4 KPI Scoring Rules

#### **IOC (Índice de Oportunidad Comercial)**
- **100**: Oportunidad identificada y gestionada perfectamente
- **50**: Oportunidad identificada pero mal gestionada
- **0**: Oportunidad ignorada o no relevante

#### **IRD (Índice de Riesgo de Deserción)**
- **100**: Hostilidad, sin solución, cliente abandona
- **50**: Incomodidad moderada, cliente insatisfecho
- **0**: Sin señales de riesgo, cliente satisfecho

#### **CES (Customer Effort Score)**
- **0**: Sin esfuerzo, proceso fluido
- **25**: Una repregunta leve
- **50**: 2 repreguntas o espera >30 segundos
- **75**: 3+ repreguntas o múltiples insistencias
- **100**: Abandono por falta de respuesta

---

## 4. CREATING CUSTOM PROMPTS

### 4.1 Step-by-Step Guide

**Step 1: Define Your Objective**
- What industry/sector are you evaluating?
- What specific behaviors matter most?
- What KPIs drive your business?

**Step 2: Create Prompt via API**
```bash
POST /api/v1/prompts
Authorization: Bearer {admin_token}

{
  "company_id": 5,
  "prompt_name": "Banking Branch Evaluation - Premium",
  "prompt_type": "dual_analysis",
  "system_prompt": "...",
  "is_active": true,
  "metadata": {
    "temperature": 0.7,
    "max_tokens": 4000,
    "industry": "banking",
    "language": "es"
  }
}
```

**Step 3: Test with Sample Evaluations**
- Submit test evaluations
- Review AI analysis quality
- Iterate on prompt wording

**Step 4: Activate for Production**
- Set `is_active: true`
- Previous active prompt auto-deactivates
- All new evaluations use new prompt

### 4.2 Prompt Template Structure

```
role: >
[Define the AI's role and expertise]

contexto: >
[Provide context about what data will be analyzed]

objetivo: >
[State the goal of the analysis]

estructura_de_salida: >
[Define the exact output format expected]

# Vista Ejecutiva
[List required sections]

# Vista Operativa
[Define JSON schema]

formato: >
[Specify how to deliver both views]
```

---

## 5. BEST PRACTICES

### 5.1 DO's ✅

1. **Be Specific:** Clearly define what behaviors to evaluate
2. **Use Examples:** Provide sample outputs in the prompt
3. **Define Scales:** Explain scoring systems (1-5, 0-100, etc.)
4. **Industry Standards:** Reference known frameworks (NPS, CES, CSAT)
5. **Structured Output:** Request consistent JSON schemas
6. **Test Thoroughly:** Validate with multiple sample evaluations
7. **Version Control:** Keep track of prompt iterations
8. **Document Changes:** Note why prompts were updated

### 5.2 DON'Ts ❌

1. **Don't Be Vague:** Avoid subjective terms without definitions
2. **Don't Overload:** Keep prompts focused (under 2000 tokens)
3. **Don't Forget JSON:** Always validate JSON schema format
4. **Don't Ignore Errors:** If AI outputs malformed data, refine prompt
5. **Don't Change Mid-Campaign:** Maintain prompt consistency during active campaigns
6. **Don't Skip Testing:** Never activate untested prompts
7. **Don't Neglect Language:** Match prompt language to transcription language

### 5.3 Optimization Tips

**For Better Executive Views:**
- Request specific emoji usage for visual clarity
- Define exact section structure
- Specify max line counts per section
- Request actionable recommendations

**For Better Operative Views:**
- Provide complete JSON schema
- Define deterministic scoring rules
- Request null handling for missing data
- Specify timestamp formats

**For Consistency:**
- Use same terminology across prompts
- Maintain standard KPI definitions
- Keep scoring scales consistent
- Document industry-specific jargon

---

## 6. INDUSTRY-SPECIFIC EXAMPLES

### 6.1 Banking & Financial Services

**Focus Areas:**
- Compliance with regulations
- Product knowledge and cross-selling
- Privacy and security handling
- Wait time management
- Professional appearance

**Custom KPIs:**
- **Compliance Score**: Verification of ID, disclosures
- **Cross-Sell Effectiveness**: Offers made vs accepted
- **Security Protocol Adherence**: Password verification, privacy

**Example Prompt Snippet:**
```
Evalúa específicamente:
1. Verificación de identidad (¿solicitó ID?)
2. Explicación de comisiones y tasas
3. Cumplimiento con normativas bancarias
4. Oferta de productos adicionales relevantes
5. Manejo seguro de información confidencial

KPI adicional - Compliance Score (0-100):
- 100: Todos los protocolos seguidos
- 50: Protocolos parcialmente cumplidos
- 0: Incumplimientos graves
```

---

### 6.2 Retail & E-commerce

**Focus Areas:**
- Product knowledge
- Upselling and cross-selling
- Store appearance and merchandising
- Checkout speed
- Returns/exchange handling

**Custom KPIs:**
- **Product Knowledge Score**: Accuracy of information
- **Sales Conversion**: Attempts to close sale
- **Store Presentation**: Cleanliness, organization

**Example Prompt Snippet:**
```
Analiza la interacción de venta al detalle:
1. Conocimiento de producto (características, precios)
2. Técnicas de venta utilizadas
3. Manejo de objeciones del cliente
4. Limpieza y organización del establecimiento
5. Proceso de pago (rapidez, errores)

KPI adicional - Sales Effectiveness (0-100):
- 100: Venta cerrada con upsell exitoso
- 50: Venta básica sin adicionales
- 0: Cliente no realizó compra
```

---

### 6.3 Hospitality & Tourism

**Focus Areas:**
- Guest greeting and farewell
- Personalization and recognition
- Problem resolution speed
- Amenity knowledge
- Cleanliness standards

**Custom KPIs:**
- **Hospitality Score**: Warmth and welcoming
- **Problem Resolution Time**: Minutes to solve issues
- **Personalization Level**: Use of guest name, preferences

**Example Prompt Snippet:**
```
Evalúa la experiencia hotelera:
1. Saludo personalizado (uso de nombre)
2. Conocimiento de servicios del hotel
3. Resolución de solicitudes especiales
4. Tiempo de respuesta a problemas
5. Despedida y seguimiento

KPI adicional - Guest Satisfaction Predictor (0-10):
- 10: Experiencia excepcional, muy probable recomendación
- 5: Experiencia estándar, cumple expectativas
- 0: Experiencia negativa, riesgo de queja pública
```

---

### 6.4 Healthcare & Medical

**Focus Areas:**
- Empathy and bedside manner
- Privacy compliance (HIPAA, GDPR)
- Clear medical explanations
- Wait time communication
- Follow-up instructions

**Custom KPIs:**
- **Empathy Score**: Emotional support provided
- **Clarity Score**: Patient understanding of diagnosis/treatment
- **Privacy Compliance**: HIPAA adherence

**Example Prompt Snippet:**
```
Analiza la interacción médico-paciente:
1. Empatía y calidez en el trato
2. Explicación clara de diagnóstico en lenguaje sencillo
3. Tiempo dedicado a escuchar síntomas
4. Privacidad y confidencialidad mantenida
5. Instrucciones de seguimiento comprensibles

KPI adicional - Patient Safety Score (0-100):
- 100: Todos los protocolos de seguridad seguidos
- 50: Protocolos parcialmente cumplidos
- 0: Riesgos de seguridad identificados
```

---

### 6.5 Call Center & Customer Support

**Focus Areas:**
- First call resolution (FCR)
- Average handle time (AHT)
- Script adherence
- Tone and empathy
- Technical knowledge

**Custom KPIs:**
- **FCR Rate**: Issue resolved in first contact
- **Script Compliance**: Key phrases used
- **Escalation Necessity**: Did issue need escalation?

**Example Prompt Snippet:**
```
Evalúa la llamada de soporte:
1. Resolución en primer contacto (FCR)
2. Uso de script de apertura y cierre
3. Conocimiento técnico del producto/servicio
4. Manejo de objeciones y clientes difíciles
5. Tiempo total de llamada vs complejidad

KPI adicional - Call Quality Score (0-100):
- 100: FCR, cliente muy satisfecho, script seguido
- 50: Solución parcial, requiere seguimiento
- 0: Sin solución, cliente molesto, escalamiento necesario
```

---

## 7. PROMPT TESTING & VALIDATION

### 7.1 Testing Checklist

Before activating a custom prompt:

- [ ] **Syntax Check:** Valid markdown/text format
- [ ] **JSON Schema:** Test JSON parsing with sample output
- [ ] **Language Consistency:** Matches transcription language
- [ ] **KPI Definitions:** Clear scoring rules (no ambiguity)
- [ ] **Sample Analysis:** Run on 3-5 test evaluations
- [ ] **Output Review:** Verify executive + operative views
- [ ] **Edge Cases:** Test with poor quality audio/transcription
- [ ] **Stakeholder Approval:** Get sign-off from CX team

### 7.2 Validation API Workflow

```bash
# 1. Create test prompt (inactive)
POST /api/v1/prompts
{
  "prompt_name": "Banking V2 - TEST",
  "is_active": false,
  ...
}

# 2. Manually test with custom prompt
# (Developer mode: force use of specific prompt_id)

# 3. Review analysis results
GET /api/v1/evaluation-analysis/{evaluation_id}

# 4. If satisfied, activate
PUT /api/v1/prompts/{prompt_id}
{
  "is_active": true
}
```

### 7.3 A/B Testing Prompts

**Strategy:** Compare two prompts over same evaluations

1. Create Prompt A (active)
2. Run evaluations for 1 week
3. Create Prompt B (inactive)
4. Activate Prompt B
5. Run same type of evaluations for 1 week
6. Compare:
   - KPI consistency
   - Actionability of recommendations
   - Stakeholder satisfaction
7. Keep best performing prompt

---

## 8. TROUBLESHOOTING

### 8.1 Common Issues

#### **Issue: JSON Parsing Errors**

**Symptom:** `operative_view` is null or malformed

**Causes:**
- Prompt doesn't clearly request JSON format
- AI generates markdown code blocks around JSON
- Schema doesn't match parsing logic

**Solution:**
```
In your prompt, add:
"CRITICAL: Output JSON without markdown code blocks. 
Do not wrap in ```json or ```. 
Start directly with { and end with }"
```

---

#### **Issue: Inconsistent Scoring**

**Symptom:** Same behaviors get different scores across evaluations

**Causes:**
- Vague scoring definitions
- Missing examples
- Temperature too high (>0.8)

**Solution:**
- Define deterministic rules: "If X happens, score is Y"
- Lower temperature to 0.5-0.7 in metadata
- Provide scoring examples in prompt

---

#### **Issue: Executive View Too Long**

**Symptom:** Wall of text, hard to read

**Causes:**
- No length limits specified
- Missing section structure

**Solution:**
```
Add to prompt:
"Resumen ejecutivo: MÁXIMO 3 líneas
Cada sección: MÁXIMO 5 bullets
Total executive view: NO EXCEDER 500 palabras"
```

---

#### **Issue: Missing Company-Specific Context**

**Symptom:** Generic analysis, doesn't reflect brand values

**Causes:**
- Prompt doesn't include company values
- Missing industry context

**Solution:**
```
Add to prompt:
"Contexto de marca:
- Valores: [list company values]
- Tono esperado: [formal/casual/friendly]
- Prioridades: [what matters most to this company]"
```

---

### 8.2 Getting Help

**For technical issues:**
- Check API error responses
- Review logs: `/var/log/supervisor/backend.err.log`
- Contact dev team

**For prompt design help:**
- Review industry examples (Section 6)
- Consult CX best practices documentation
- Request prompt audit from CX consultants

---

## APPENDIX A: PROMPT METADATA OPTIONS

```json
{
  "temperature": 0.7,           // Creativity (0.0-1.0, default 0.7)
  "max_tokens": 4000,           // Max response length
  "industry": "banking",         // Industry tag
  "language": "es",              // Primary language
  "version": "2.0",              // Prompt version for tracking
  "author": "CX Team",           // Who created it
  "tested_on": "2025-01-15",    // Last validation date
  "notes": "Optimized for branch evaluations"
}
```

---

## APPENDIX B: GPT-4o Limits

- **Max Input Tokens:** ~128,000 (includes prompt + transcription)
- **Max Output Tokens:** 4,096 (can be increased to 16k)
- **Recommended:** Keep prompts under 2,000 tokens
- **Transcriptions:** Typically 500-2,000 tokens (5-15 min video)

**Token Estimation:**
- 1 token ≈ 0.75 words (Spanish)
- 1 token ≈ 4 characters

---

**End of Prompt Reference Documentation**

For API usage, see `API_REFERENCE.md`  
For system architecture, see `ARCHITECTURE_MASTER.md`
