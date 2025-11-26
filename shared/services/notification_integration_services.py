"""
Notification Integration Services
Email (SendGrid) and SMS (Twilio) integrations
"""

import os
from typing import Dict, List
from app.core.config import settings


# ===== EMAIL NOTIFICATIONS (SendGrid) =====

class EmailService:
    """SendGrid email service integration"""
    
    def __init__(self):
        # Note: SendGrid API key should be in environment variables
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@sieteic.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Siete CX")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str | None = None
    ) -> bool:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text fallback (optional)
        
        Returns:
            bool: Success status
        """
        
        if not self.api_key:
            print("⚠️ SendGrid API key not configured")
            return False
        
        try:
            # Import SendGrid (requires: pip install sendgrid)
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            if plain_content:
                message.add_content(Content("text/plain", plain_content))
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            return response.status_code == 202
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    async def send_evaluation_complete_email(
        self,
        to_email: str,
        user_name: str,
        evaluation_id: int,
        campaign_name: str
    ) -> bool:
        """Send notification when evaluation analysis is complete"""
        
        subject = f"Evaluación #{evaluation_id} - Análisis Completado"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #8b5cf6; 
                          color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Análisis Completado</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{user_name}</strong>,</p>
                    
                    <p>Tu evaluación <strong>#{evaluation_id}</strong> para la campaña 
                    <strong>{campaign_name}</strong> ha sido analizada por nuestro sistema de IA.</p>
                    
                    <p><strong>Análisis disponible:</strong></p>
                    <ul>
                        <li>Vista Ejecutiva con insights narrativos</li>
                        <li>Vista Operativa con KPIs y métricas</li>
                        <li>Recomendaciones accionables</li>
                        <li>Tags automáticos aplicados</li>
                    </ul>
                    
                    <a href="https://cx.sieteic.com/evaluations/{evaluation_id}" class="button">
                        Ver Análisis Completo
                    </a>
                </div>
                <div class="footer">
                    <p>© 2025 Siete Inteligencia Creativa | Siete CX Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_content = f"""
        Hola {user_name},
        
        Tu evaluación #{evaluation_id} para la campaña {campaign_name} ha sido analizada.
        
        Análisis disponible:
        - Vista Ejecutiva con insights narrativos
        - Vista Operativa con KPIs y métricas
        - Recomendaciones accionables
        
        Ver en: https://cx.sieteic.com/evaluations/{evaluation_id}
        
        © 2025 Siete Inteligencia Creativa
        """
        
        return await self.send_email(to_email, subject, html_content, plain_content)
    
    async def send_insight_alert_email(
        self,
        to_email: str,
        user_name: str,
        insight_title: str,
        insight_description: str,
        severity: str
    ) -> bool:
        """Send email alert for critical insights"""
        
        severity_colors = {
            "critical": "#ef4444",
            "high": "#f59e0b",
            "medium": "#3b82f6",
            "low": "#6b7280"
        }
        
        severity_icons = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "ℹ️",
            "low": "📊"
        }
        
        color = severity_colors.get(severity, "#6b7280")
        icon = severity_icons.get(severity, "📊")
        
        subject = f"{icon} Alerta CX - {insight_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert {{ background: {color}; color: white; padding: 20px; border-radius: 8px; }}
                .content {{ background: #f9fafb; padding: 20px; margin-top: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert">
                    <h2>{icon} {insight_title}</h2>
                    <p>Severidad: <strong>{severity.upper()}</strong></p>
                </div>
                <div class="content">
                    <p>Hola {user_name},</p>
                    <p>{insight_description}</p>
                    <p><a href="https://cx.sieteic.com/intelligence">Ver Detalles</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)


# ===== SMS NOTIFICATIONS (Twilio) =====

class SMSService:
    """Twilio SMS service integration"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> bool:
        """
        Send SMS via Twilio
        
        Args:
            to_number: Recipient phone number (E.164 format: +1234567890)
            message: SMS message content (max 160 chars for single SMS)
        
        Returns:
            bool: Success status
        """
        
        if not self.account_sid or not self.auth_token:
            print("⚠️ Twilio credentials not configured")
            return False
        
        try:
            # Import Twilio (requires: pip install twilio)
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return message.sid is not None
            
        except Exception as e:
            print(f"❌ Error sending SMS: {e}")
            return False
    
    async def send_critical_alert_sms(
        self,
        to_number: str,
        alert_title: str
    ) -> bool:
        """Send SMS for critical alerts"""
        
        message = f"🚨 Siete CX Alert: {alert_title}. Revisa tu dashboard: https://cx.sieteic.com"
        return await self.send_sms(to_number, message)


# ===== IN-APP PUSH NOTIFICATIONS =====

async def create_in_app_notification(
    session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    related_entity_id: int | None = None
):
    """
    Create in-app notification in database
    
    This uses the existing notification_model
    """
    from app.models.notification_model import Notification
    from datetime import datetime
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_entity_id=related_entity_id,
        is_read=False,
        created_at=datetime.now()
    )
    
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    
    return notification


# ===== NOTIFICATION ORCHESTRATOR =====

class NotificationOrchestrator:
    """
    Orchestrates multi-channel notifications
    Sends via email, SMS, and in-app based on user preferences
    """
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    async def notify_evaluation_complete(
        self,
        session,
        user_id: int,
        user_email: str,
        user_name: str,
        user_phone: str | None,
        evaluation_id: int,
        campaign_name: str,
        preferences: Dict = None
    ):
        """
        Send multi-channel notification for evaluation completion
        
        Args:
            preferences: {"email": bool, "sms": bool, "in_app": bool}
        """
        
        if preferences is None:
            preferences = {"email": True, "sms": False, "in_app": True}
        
        results = {}
        
        # In-app notification (always sent)
        if preferences.get("in_app", True):
            await create_in_app_notification(
                session,
                user_id,
                "Evaluación Analizada",
                f"Tu evaluación #{evaluation_id} para {campaign_name} ha sido analizada por IA.",
                notification_type="success",
                related_entity_id=evaluation_id
            )
            results["in_app"] = True
        
        # Email notification
        if preferences.get("email", True):
            email_sent = await self.email_service.send_evaluation_complete_email(
                user_email, user_name, evaluation_id, campaign_name
            )
            results["email"] = email_sent
        
        # SMS notification (optional)
        if preferences.get("sms", False) and user_phone:
            sms_message = f"Siete CX: Tu evaluación #{evaluation_id} ha sido analizada. Ver: https://cx.sieteic.com/evaluations/{evaluation_id}"
            sms_sent = await self.sms_service.send_sms(user_phone, sms_message)
            results["sms"] = sms_sent
        
        return results
    
    async def notify_critical_insight(
        self,
        session,
        user_id: int,
        user_email: str,
        user_name: str,
        user_phone: str | None,
        insight_title: str,
        insight_description: str,
        preferences: Dict = None
    ):
        """Send multi-channel notification for critical insights"""
        
        if preferences is None:
            preferences = {"email": True, "sms": True, "in_app": True}
        
        results = {}
        
        # In-app notification
        if preferences.get("in_app", True):
            await create_in_app_notification(
                session,
                user_id,
                f"🚨 {insight_title}",
                insight_description,
                notification_type="alert"
            )
            results["in_app"] = True
        
        # Email alert
        if preferences.get("email", True):
            email_sent = await self.email_service.send_insight_alert_email(
                user_email, user_name, insight_title, insight_description, "critical"
            )
            results["email"] = email_sent
        
        # SMS alert
        if preferences.get("sms", True) and user_phone:
            sms_sent = await self.sms_service.send_critical_alert_sms(
                user_phone, insight_title
            )
            results["sms"] = sms_sent
        
        return results


# Singleton instances
email_service = EmailService()
sms_service = SMSService()
notification_orchestrator = NotificationOrchestrator()
