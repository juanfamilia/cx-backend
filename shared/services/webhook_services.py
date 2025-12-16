"""
Webhook Services - Outbound webhooks for external integrations
Supports: Slack, Generic HTTP webhooks, future integrations
"""
import httpx
from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from shared.core.config import settings
from shared.models.company_model import Company


class SlackService:
    """Slack webhook integration"""
    
    def __init__(self):
        self.default_webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
    
    async def send_message(
        self,
        message: str,
        webhook_url: str | None = None,
        channel: str | None = None,
        username: str = "Siete CX Bot",
        icon_emoji: str = ":robot_face:",
        attachments: list[dict] | None = None
    ) -> bool:
        """Send a message to Slack"""
        url = webhook_url or self.default_webhook_url
        if not url:
            print("⚠️ No Slack webhook URL configured")
            return False
        
        payload = {
            "text": message,
            "username": username,
            "icon_emoji": icon_emoji
        }
        
        if channel:
            payload["channel"] = channel
        
        if attachments:
            payload["attachments"] = attachments
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending Slack message: {e}")
            return False
    
    async def send_critical_alert(
        self,
        title: str,
        description: str,
        severity: str,
        evaluation_id: int,
        webhook_url: str | None = None
    ) -> bool:
        """Send a critical alert to Slack with rich formatting"""
        
        color_map = {
            "critical": "#dc2626",  # red
            "high": "#f97316",      # orange
            "medium": "#eab308",    # yellow
            "low": "#3b82f6"        # blue
        }
        
        attachments = [{
            "color": color_map.get(severity, "#6b7280"),
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severidad:*\n{severity.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Evaluación:*\n#{evaluation_id}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Descripción:*\n{description}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }]
        
        return await self.send_message(
            message=f"🚨 Alerta: {title}",
            webhook_url=webhook_url,
            attachments=attachments
        )


class WebhookService:
    """Generic HTTP webhook service"""
    
    async def send_webhook(
        self,
        url: str,
        event_type: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        secret: str | None = None
    ) -> tuple[bool, int | None, str | None]:
        """
        Send a webhook to an external URL
        
        Returns: (success, status_code, error_message)
        """
        
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": payload
        }
        
        request_headers = {
            "Content-Type": "application/json",
            "User-Agent": "SieteCX-Webhook/1.0"
        }
        
        if headers:
            request_headers.update(headers)
        
        if secret:
            import hmac
            import hashlib
            import json
            signature = hmac.new(
                secret.encode(),
                json.dumps(webhook_payload).encode(),
                hashlib.sha256
            ).hexdigest()
            request_headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=webhook_payload,
                    headers=request_headers,
                    timeout=30.0
                )
                
                if response.status_code >= 200 and response.status_code < 300:
                    return True, response.status_code, None
                else:
                    return False, response.status_code, response.text
                    
        except httpx.TimeoutException:
            return False, None, "Timeout"
        except Exception as e:
            return False, None, str(e)
    
    async def send_insight_webhook(
        self,
        url: str,
        insight_type: str,
        severity: str,
        title: str,
        description: str,
        evaluation_id: int,
        company_id: int,
        metrics: dict | None = None,
        suggested_actions: list[str] | None = None,
        secret: str | None = None
    ) -> tuple[bool, int | None, str | None]:
        """Send an insight event webhook"""
        
        payload = {
            "insight_type": insight_type,
            "severity": severity,
            "title": title,
            "description": description,
            "evaluation_id": evaluation_id,
            "company_id": company_id,
            "metrics": metrics or {},
            "suggested_actions": suggested_actions or []
        }
        
        return await self.send_webhook(
            url=url,
            event_type="insight.created",
            payload=payload,
            secret=secret
        )
    
    async def send_evaluation_complete_webhook(
        self,
        url: str,
        evaluation_id: int,
        campaign_id: int,
        evaluator_id: int,
        score: float,
        company_id: int,
        secret: str | None = None
    ) -> tuple[bool, int | None, str | None]:
        """Send an evaluation complete event webhook"""
        
        payload = {
            "evaluation_id": evaluation_id,
            "campaign_id": campaign_id,
            "evaluator_id": evaluator_id,
            "score": score,
            "company_id": company_id
        }
        
        return await self.send_webhook(
            url=url,
            event_type="evaluation.completed",
            payload=payload,
            secret=secret
        )


class IntegrationOrchestrator:
    """
    Orchestrates outbound integrations (webhooks, Slack, etc.)
    based on company configuration
    """
    
    def __init__(self):
        self.slack = SlackService()
        self.webhook = WebhookService()
    
    async def notify_critical_insight(
        self,
        session: AsyncSession,
        company_id: int,
        insight_type: str,
        severity: str,
        title: str,
        description: str,
        evaluation_id: int,
        metrics: dict | None = None,
        suggested_actions: list[str] | None = None
    ):
        """
        Send notifications through all configured channels for a company
        """
        
        # Get company settings
        query = select(Company).where(Company.id == company_id)
        result = await session.execute(query)
        company = result.scalars().first()
        
        if not company:
            return
        
        # Check for Slack webhook in company settings (if stored)
        slack_url = getattr(company, 'slack_webhook_url', None)
        if slack_url:
            await self.slack.send_critical_alert(
                title=title,
                description=description,
                severity=severity,
                evaluation_id=evaluation_id,
                webhook_url=slack_url
            )
        
        # Check for generic webhook URL
        webhook_url = getattr(company, 'webhook_url', None)
        webhook_secret = getattr(company, 'webhook_secret', None)
        if webhook_url:
            await self.webhook.send_insight_webhook(
                url=webhook_url,
                insight_type=insight_type,
                severity=severity,
                title=title,
                description=description,
                evaluation_id=evaluation_id,
                company_id=company_id,
                metrics=metrics,
                suggested_actions=suggested_actions,
                secret=webhook_secret
            )


# Singleton instances
slack_service = SlackService()
webhook_service = WebhookService()
integration_orchestrator = IntegrationOrchestrator()
