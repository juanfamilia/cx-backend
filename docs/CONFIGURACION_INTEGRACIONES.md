# 🚀 Guía de Configuración - Siete CX Enterprise

Esta guía te ayudará a configurar todas las integraciones enterprise de Siete CX.

---

## 📧 1. SendGrid (Email)

### Obtener API Key:
1. Ve a [SendGrid](https://sendgrid.com) y crea una cuenta
2. Ve a **Settings > API Keys**
3. Click en **Create API Key**
4. Selecciona **Full Access** o **Restricted Access** (con permisos de Mail Send)
5. Copia la API Key generada

### Variables de entorno en Railway:
```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@tudominio.com
SENDGRID_FROM_NAME=Siete CX
```

### Verificar dominio (recomendado):
1. En SendGrid, ve a **Settings > Sender Authentication**
2. Configura **Domain Authentication** para mejor entregabilidad

---

## 📱 2. Twilio (SMS)

### Obtener credenciales:
1. Ve a [Twilio Console](https://console.twilio.com)
2. En el Dashboard, copia:
   - **Account SID** (empieza con AC...)
   - **Auth Token** (click en "Show" para verlo)
3. Ve a **Phone Numbers > Manage > Buy a number**
4. Compra un número con capacidad de SMS

### Variables de entorno en Railway:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1234567890
```

### Nota sobre números:
- El número debe estar en formato E.164: `+1234567890`
- Para República Dominicana: `+18091234567`

---

## 💬 3. Slack Webhooks

### Crear Webhook:
1. Ve a [Slack API](https://api.slack.com/apps)
2. Click en **Create New App > From scratch**
3. Nombra tu app "Siete CX Alerts" y selecciona tu workspace
4. Ve a **Incoming Webhooks** y actívalo
5. Click en **Add New Webhook to Workspace**
6. Selecciona el canal donde quieres recibir alertas
7. Copia la **Webhook URL**

### Variables de entorno en Railway:
```
SLACK_WEBHOOK_URL=<tu-webhook-url-de-slack>
```

**Formato del webhook:** `https://hooks.slack.com/services/...`

### Configuración por empresa (opcional):
Cada empresa puede tener su propio webhook configurado en su perfil.
Los campos en la tabla `companies`:
- `slack_webhook_url`: URL del webhook de Slack
- `webhook_url`: URL de webhook genérico
- `webhook_secret`: Secret para firmar webhooks

---

## ⏰ 4. Cron Jobs (Railway)

### Configurar Weekly Digest:

1. En Railway, ve a tu proyecto
2. Click en **+ New** > **Cron Job**
3. Configura:
   - **Name**: `weekly-digest`
   - **Schedule**: `0 8 * * 1` (Lunes a las 8:00 AM)
   - **Command**: 
   ```bash
   curl -X POST https://tu-api-url.railway.app/api/v1/jobs/weekly-digest \
     -H "X-Cron-Secret: tu-cron-secret"
   ```

### Variables de entorno:
```
CRON_SECRET=un-secret-seguro-aleatorio
```

### Endpoints disponibles:
| Endpoint | Descripción |
|----------|-------------|
| `POST /api/v1/jobs/weekly-digest` | Envía digest a todas las empresas |
| `POST /api/v1/jobs/weekly-digest/{company_id}` | Envía digest a una empresa específica |
| `GET /api/v1/jobs/health` | Health check del servicio de cron |

### Probar manualmente:
```bash
curl -X POST https://siete-api-staging.up.railway.app/api/v1/jobs/weekly-digest \
  -H "X-Cron-Secret: tu-cron-secret"
```

---

## 🤖 5. OpenAI (Análisis de IA)

### Obtener API Key:
1. Ve a [OpenAI Platform](https://platform.openai.com)
2. Ve a **API Keys**
3. Click en **Create new secret key**
4. Copia la key generada

### Variables de entorno en Railway:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Modelos utilizados:
- **Whisper-1**: Transcripción de audio
- **GPT-4o**: Análisis de transcripciones

---

## 🔧 Resumen de Variables de Entorno

Agrega estas variables en **Railway > Variables**:

```env
# Email (SendGrid)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@sieteic.com
SENDGRID_FROM_NAME=Siete CX

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+18091234567

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx

# Cron Jobs
CRON_SECRET=genera-un-secret-seguro-aqui

# OpenAI (si no está configurado)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Analysis Service (interno Railway)
ANALYSIS_SERVICE_URL=http://siete-analysis.railway.internal
```

---

## ✅ Verificación

### 1. Verificar configuración:
```bash
# Health check
curl https://tu-api.railway.app/health

# Verificar cron endpoint
curl https://tu-api.railway.app/api/v1/jobs/health
```

### 2. Probar email (desde código):
```python
from shared.services.notification_integration_services import email_service

# Test
result = await email_service.send_email(
    to_email="tu@email.com",
    subject="Test Siete CX",
    html_content="<h1>Funciona!</h1>"
)
print(f"Email sent: {result}")
```

### 3. Probar Slack:
```python
from shared.services.webhook_services import slack_service

result = await slack_service.send_message(
    message="🧪 Test desde Siete CX",
    webhook_url="tu-webhook-url"
)
print(f"Slack sent: {result}")
```

---

## 🔄 Flujo de Notificaciones

```
Evaluación Completada
        │
        ▼
   ┌────────────────┐
   │ Análisis de IA │
   │  (OpenAI)      │
   └────────┬───────┘
            │
            ▼
   ┌────────────────┐
   │ Generar        │
   │ Insights       │
   └────────┬───────┘
            │
            ▼
   ┌────────────────────────────────────────┐
   │         Notification Orchestrator       │
   │                                         │
   │  ┌─────────┐ ┌─────────┐ ┌──────────┐  │
   │  │  Email  │ │   SMS   │ │  In-App  │  │
   │  │SendGrid │ │ Twilio  │ │   DB     │  │
   │  └─────────┘ └─────────┘ └──────────┘  │
   │                                         │
   │  ┌─────────┐ ┌──────────────────────┐  │
   │  │  Slack  │ │  Webhooks Genéricos  │  │
   │  └─────────┘ └──────────────────────┘  │
   └────────────────────────────────────────┘
```

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que las variables de entorno estén correctamente configuradas
2. Revisa los logs en Railway
3. Prueba los endpoints de health check

---

*Última actualización: Diciembre 2024*
