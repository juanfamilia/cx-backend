"""
Integration Test Router
Endpoints to test email, SMS, and webhook integrations
Only available in non-production environments
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os

from shared.core.db import get_db
from shared.core.config import settings
from shared.services.notification_integration_services import email_service, sms_service
from shared.services.webhook_services import slack_service


router = APIRouter(
    prefix="/integration-test",
    tags=["Integration Tests"],
)


class EmailTestRequest(BaseModel):
    to_email: str
    subject: str = "Test Email - Siete CX"
    message: str = "Este es un email de prueba desde Siete CX."


class SMSTestRequest(BaseModel):
    to_number: str  # E.164 format: +1234567890
    message: str = "Test SMS desde Siete CX"


class SlackTestRequest(BaseModel):
    message: str = "🧪 Test message from Siete CX"
    webhook_url: str | None = None


def check_non_production():
    """Only allow in staging/development"""
    env_mode = os.getenv("ENV_MODE", "staging")
    if env_mode == "production":
        raise HTTPException(
            status_code=403, 
            detail="Integration tests disabled in production"
        )
    return True


@router.get("/status", summary="Check integration configuration status")
async def check_integration_status(_: bool = Depends(check_non_production)):
    """Check which integrations are configured"""
    return {
        "email": {
            "provider": "SendGrid",
            "configured": bool(settings.SENDGRID_API_KEY),
            "from_email": settings.SENDGRID_FROM_EMAIL,
            "from_name": settings.SENDGRID_FROM_NAME
        },
        "sms": {
            "provider": "Twilio",
            "configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
            "from_number": settings.TWILIO_FROM_NUMBER or "NOT SET"
        },
        "slack": {
            "provider": "Slack Webhooks",
            "default_configured": bool(settings.SLACK_WEBHOOK_URL)
        },
        "openai": {
            "provider": "OpenAI",
            "configured": bool(settings.OPENAI_API_KEY)
        },
        "cron": {
            "secret_configured": settings.CRON_SECRET != "siete-cx-cron-secret-change-me"
        }
    }


@router.post("/email", summary="Test email sending")
async def test_email(
    request: EmailTestRequest,
    _: bool = Depends(check_non_production)
):
    """Send a test email via SendGrid"""
    
    if not settings.SENDGRID_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="SendGrid API key not configured. Set SENDGRID_API_KEY in environment."
        )
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #3b82f6;">🧪 Test Email - Siete CX</h2>
        <p>{request.message}</p>
        <hr>
        <p style="color: #6b7280; font-size: 12px;">
            Este es un email de prueba enviado desde el sistema de integración.
        </p>
    </div>
    """
    
    success = await email_service.send_email(
        to_email=request.to_email,
        subject=request.subject,
        html_content=html_content,
        plain_content=request.message
    )
    
    return {
        "success": success,
        "to": request.to_email,
        "subject": request.subject,
        "provider": "SendGrid"
    }


@router.post("/sms", summary="Test SMS sending")
async def test_sms(
    request: SMSTestRequest,
    _: bool = Depends(check_non_production)
):
    """Send a test SMS via Twilio"""
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        )
    
    if not settings.TWILIO_FROM_NUMBER:
        raise HTTPException(
            status_code=400,
            detail="Twilio from number not configured. Set TWILIO_FROM_NUMBER."
        )
    
    success = await sms_service.send_sms(
        to_number=request.to_number,
        message=request.message
    )
    
    return {
        "success": success,
        "to": request.to_number,
        "from": settings.TWILIO_FROM_NUMBER,
        "provider": "Twilio"
    }


@router.post("/slack", summary="Test Slack webhook")
async def test_slack(
    request: SlackTestRequest,
    _: bool = Depends(check_non_production)
):
    """Send a test message to Slack"""
    
    webhook_url = request.webhook_url or settings.SLACK_WEBHOOK_URL
    
    if not webhook_url:
        raise HTTPException(
            status_code=400,
            detail="No Slack webhook URL provided or configured."
        )
    
    success = await slack_service.send_message(
        message=request.message,
        webhook_url=webhook_url,
        username="Siete CX Test Bot",
        icon_emoji=":test_tube:"
    )
    
    return {
        "success": success,
        "webhook_url": webhook_url[:50] + "...",
        "provider": "Slack"
    }


@router.post("/slack/alert", summary="Test Slack critical alert")
async def test_slack_alert(
    _: bool = Depends(check_non_production)
):
    """Send a test critical alert to Slack"""
    
    if not settings.SLACK_WEBHOOK_URL:
        raise HTTPException(
            status_code=400,
            detail="Default Slack webhook URL not configured."
        )
    
    success = await slack_service.send_critical_alert(
        title="Test Critical Alert",
        description="Este es un mensaje de prueba para verificar las alertas críticas de Siete CX.",
        severity="high",
        evaluation_id=12345,
        webhook_url=settings.SLACK_WEBHOOK_URL
    )
    
    return {
        "success": success,
        "alert_type": "critical",
        "provider": "Slack"
    }
