# 🔄 MAPA DEL FLUJO NO NEGOCIABLE - SIETE CX

## Flujo Completo: Video → Insights

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO NO NEGOCIABLE                                │
└─────────────────────────────────────────────────────────────────────────────┘

   PASO 1                PASO 2              PASO 3              PASO 4
┌──────────┐         ┌──────────┐        ┌──────────┐       ┌──────────┐
│  VIDEO   │────────▶│ METADATA │───────▶│   JOB    │──────▶│ WHISPER  │
│Cloudflare│         │  Backend │        │ ASYNC    │       │Transcribe│
│ Stream   │         │          │        │          │       │          │
└──────────┘         └──────────┘        └──────────┘       └──────────┘
     │                    │                   │                  │
     │                    │                   │                  │
     ▼                    ▼                   ▼                  ▼
  Frontend            PostgreSQL         BackgroundTask      OpenAI API
  TUS Upload          evaluation,        extract_audio       whisper-1
                      video tables       services.py


   PASO 5                PASO 6              PASO 7              PASO 8
┌──────────┐         ┌──────────┐        ┌──────────┐       ┌──────────┐
│   GPT    │────────▶│  CLIPS   │───────▶│PRIORIZAR │──────▶│ INSIGHTS │
│ Análisis │         │  (Auto)  │        │  CLIPS   │       │ + CLIPS  │
│          │         │          │        │          │       │ Cliente  │
└──────────┘         └──────────┘        └──────────┘       └──────────┘
     │                    │                   │                  │
     │                    │                   │                  │
     ▼                    ▼                   ▼                  ▼
  OpenAI API          ❌ NO EXISTE        ❌ NO EXISTE       Dashboard +
  gpt-4o              PENDIENTE          PENDIENTE          Notifications
  Vista Ejecutiva                                           (parcial)
  Vista Operativa
```

---

## Estado Actual de Cada Paso

### ✅ PASO 1: Video a Cloudflare Stream
**Estado:** FUNCIONAL
**Archivos:**
- `app/routes/cloudflare_router.py` - Genera URL de upload
- Frontend usa TUS protocol para subir directamente

**Flujo:**
1. Frontend solicita token de upload (`POST /cloudflare/stream`)
2. Backend retorna `upload_url` de Cloudflare
3. Frontend sube video directamente a Cloudflare (TUS)
4. Cloudflare retorna `uid` del video

**Requisitos:** 
- ✅ `CLOUDFLARE_ACCOUNT_ID` 
- ✅ `CLOUDFLARE_STREAM_KEY`

---

### ✅ PASO 2: Backend guarda Metadata
**Estado:** FUNCIONAL
**Archivos:**
- `app/routes/evaluation_router.py` - `POST /evaluations/`
- `shared/services/evaluation_services.py`
- `shared/services/video_services.py`

**Flujo:**
1. Frontend envía: `media_url` (uid), `video_title`, `campaign_id`, `evaluation_answers`
2. Backend crea registro en `videos` con URL de Cloudflare
3. Backend crea registro en `evaluations` con metadata
4. Retorna `evaluation_id`

**Estados de Evaluation:**
- `enviado` → Inicial
- `editar` → Pendiente revisión
- `actualizado` → Modificado
- `aprobado` → Validado
- `rechazado` → Rechazado

---

### ✅ PASO 3: Job Asíncrono extrae Audio
**Estado:** FUNCIONAL
**Archivos:**
- `analysis/services/extract_audio_services.py` - `handle_stream_to_audio()`
- `shared/services/cloudflare_stream_services.py`
- `shared/services/cloudflare_rs_services.py` (R2 storage)

**Flujo:**
1. `BackgroundTask` llama `handle_stream_to_audio(video_uid, evaluation_id, session)`
2. Espera que Cloudflare tenga video `readyToStream`
3. Habilita descarga en Cloudflare
4. Descarga video a `/tmp/`
5. Extrae audio con `moviepy`
6. Sube audio a Cloudflare R2

**Requisitos:**
- ✅ `CLOUDFLARE_ACCOUNT_ID`
- ✅ `CLOUDFLARE_STREAM_KEY`
- ✅ `R2_ACCESS_KEY_ID`
- ✅ `R2_SECRET_ACCESS_KEY`
- ✅ `R2_BUCKET`
- ✅ `R2_ENDPOINT_URL`

---

### ✅ PASO 4: Whisper transcribe Audio
**Estado:** FUNCIONAL
**Archivos:**
- `analysis/services/openai_services.py` - `audio_analysis()`

**Flujo:**
1. Lee archivo de audio
2. Llama `client.audio.transcriptions.create(model="whisper-1")`
3. Retorna transcripción en español

**Requisitos:**
- ✅ `OPENAI_API_KEY`

---

### ✅ PASO 5: GPT analiza Transcripción
**Estado:** FUNCIONAL
**Archivos:**
- `analysis/services/openai_services.py` - `audio_analysis()`
- `shared/services/prompt_manager_services.py` - Prompts personalizados

**Flujo:**
1. Usa transcripción del paso anterior
2. Aplica prompt de sistema (default o custom por empresa)
3. Llama `client.chat.completions.create(model="gpt-4o")`
4. Genera:
   - **Vista Ejecutiva:** Narrativa con insights, emociones, NPS inferido
   - **Vista Operativa JSON:** IOC, IRD, CES, Verbatims con timestamps

**Output JSON esperado:**
```json
{
  "IOC": {"score": 0-100, "justificacion": "..."},
  "IRD": {"score": 0-100, "justificacion": "..."},
  "CES": {"score": 0-100, "justificacion": "..."},
  "Verbatims": {
    "positivos": [{"texto": "...", "timestamp": "mm:ss", "origen": "cliente"}],
    "negativos": [...],
    "criticos": [...]
  },
  "acciones_sugeridas": [...]
}
```

---

### ✅ PASO 6: Generación de Clips Automáticos
**Estado:** IMPLEMENTADO (Nuevo)
**Archivos:**
- `analysis/services/clip_generation_services.py` - Servicio principal
- `shared/models/clip_model.py` - Modelos Clip y ClipConfig
- `analysis/routes/clip_router.py` - Endpoints API
- `app/migrations/versions/20250202_add_clips_tables.py` - Migración BD

**Flujo:**
1. Parsea Verbatims del JSON de GPT (críticos, negativos, positivos)
2. Convierte timestamps `mm:ss` a segundos
3. Calcula boundaries según configuración:
   - Críticos: 10s antes + 20s después
   - Negativos: 5s antes + 15s después
   - Positivos: 5s antes + 10s después
4. Descarga video original de Cloudflare
5. Extrae clips con FFmpeg/moviepy
6. Sube cada clip a Cloudflare Stream
7. Guarda en BD con priority_score

**Límites:**
- Max 60 segundos por clip
- Configurable por empresa (`clip_configs` table)

**Endpoints:**
- `GET /clips/evaluation/{id}` - Clips de una evaluación
- `GET /clips/evaluation/{id}/status` - Estado de procesamiento
- `GET /clips/{id}` - Clip individual

---

### ⚠️ PASO 7: Priorización de Clips
**Estado:** IMPLEMENTADO (Integrado en Paso 6)
**Archivos:**
- `analysis/services/clip_generation_services.py` - `calculate_priority_score()`

**Lógica de Scoring:**
```
Base:
- Críticos: 100 puntos
- Negativos: 50 puntos
- Positivos: 10 puntos

Bonus (del contexto):
- IRD score: hasta +30 puntos
- CES score: hasta +20 puntos
```

**Entrega:**
- Se generan TODOS los clips
- Se entregan al cliente solo los Top N (default: 5)
- Campo `is_delivered` marca cuáles se muestran
- Campo `priority_rank` indica el orden

---

### ⚠️ PASO 8: Entrega de Insights + Clips
**Estado:** PARCIAL
**Lo que existe:**
- ✅ Dashboard con métricas básicas
- ✅ Lista de insights (`/intelligence/insights`)
- ✅ Notificaciones in-app
- ⚙️ Email/SMS/Slack (código existe, falta configurar)
- ❌ Vista de clips priorizados
- ❌ Exportación de reportes con clips

**Archivos existentes:**
- `app/routes/intelligence_router.py`
- `shared/services/intelligence_services.py`
- `app/routes/dashboard_router.py`

---

## 🔴 RESUMEN: QUÉ FALTA PARA EL FLUJO COMPLETO

### CRÍTICO (Bloquea el flujo)
| # | Componente | Estado | Esfuerzo |
|---|------------|--------|----------|
| 1 | **Generación de Clips** | ✅ Implementado | - |
| 2 | **Modelo de Clips en BD** | ✅ Implementado | - |
| 3 | **Priorización de Clips** | ✅ Implementado | - |
| 4 | **UI para ver Clips** | ❌ Pendiente (Frontend) | 2-3 días |

### CONFIGURACIÓN (Funcional pero no activo)
| # | Componente | Estado | Esfuerzo |
|---|------------|--------|----------|
| 5 | SendGrid API Key | ⚙️ Falta key | 10 min |
| 6 | Twilio API Keys | ⚙️ Falta keys | 10 min |
| 7 | Slack Webhook | ⚙️ Falta URL | 10 min |
| 8 | Cron Job Railway | ⚙️ Falta config | 15 min |
| 9 | **Migración BD (clips)** | ⚙️ Ejecutar en deploy | 5 min |

### MEJORAS (No bloquea pero mejora UX)
| # | Componente | Estado | Esfuerzo |
|---|------------|--------|----------|
| 9 | Webhook de Cloudflare | ⚠️ No implementado | 1 día |
| 10 | Estado de procesamiento | ⚠️ No visible al usuario | 1 día |
| 11 | Reportes PDF | ⚠️ No existe | 2-3 días |

---

## 📋 ORDEN DE IMPLEMENTACIÓN SUGERIDO

### Fase 1: Completar el Core (Clips)
1. Crear modelo `Clip` en BD
2. Implementar `clip_generation_services.py`
3. Parsear timestamps de GPT
4. Generar clips con FFmpeg/moviepy
5. Guardar en R2 y BD

### Fase 2: Priorización
1. Implementar scoring de clips
2. Crear endpoint `/clips/prioritized`
3. UI básica para ver clips

### Fase 3: Configuración
1. Configurar API keys en Railway
2. Activar cron jobs
3. Probar notificaciones

### Fase 4: Polish
1. Webhook de Cloudflare (estado en tiempo real)
2. Indicadores de progreso en UI
3. Reportes exportables

---

## ⚠️ RIESGOS IDENTIFICADOS

1. **FFmpeg en Railway:** Verificar que esté instalado en el Dockerfile
2. **Memoria/CPU:** Generación de clips consume recursos
3. **Almacenamiento R2:** Clips ocupan espacio, considerar política de retención
4. **Rate Limits OpenAI:** Videos largos = mucho audio = costos
5. **Sesión de BD en BackgroundTask:** Actualmente pasa `session`, puede causar problemas de conexión

---

*Documento generado: Diciembre 2024*
