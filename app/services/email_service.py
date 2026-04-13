"""
Email Service — Hostinger SMTP
Envío de correos transaccionales para notificaciones de workflow.

Configuración requerida en .env / Railway:
  SMTP_ENABLED=true
  SMTP_USER=notificaciones@sieteic.com
  SMTP_PASSWORD=<contraseña>
  SMTP_FROM_NAME=Siete CX          # opcional, default "Siete CX"
  SMTP_HOST=smtp.hostinger.com     # default
  SMTP_PORT=465                    # 465=SSL, 587=STARTTLS
"""

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core sender (sync, runs in thread pool)
# ---------------------------------------------------------------------------

def _send_sync(
    to_addresses: List[str],
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    if not settings.SMTP_ENABLED:
        logger.info("SMTP disabled — email not sent to %s | subject: %s", to_addresses, subject)
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email")
        return

    from_addr = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addresses)

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()

    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, to_addresses, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, to_addresses, msg.as_string())

        logger.info("Email sent to %s | subject: %s", to_addresses, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_addresses, exc)


async def send_email(
    to_addresses: List[str],
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    await run_in_threadpool(_send_sync, to_addresses, subject, html_body, text_body)


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

_BASE_STYLE = """
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1a1a2e; background: #f4f6f9; padding: 32px 0;
"""

def _wrap(inner: str, footer: str = "") -> str:
    return f"""
    <div style="{_BASE_STYLE}">
      <div style="max-width:580px;margin:0 auto;background:#fff;border-radius:12px;
                  overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);">
        <div style="background:#1a1a2e;padding:24px 32px;">
          <span style="color:#fff;font-size:20px;font-weight:700;">Siete CX</span>
        </div>
        <div style="padding:32px;">
          {inner}
        </div>
        {f'<div style="background:#f4f6f9;padding:16px 32px;font-size:12px;color:#888;">{footer}</div>' if footer else ''}
      </div>
    </div>
    """


def email_evaluation_approved(
    evaluator_name: str,
    evaluation_id: int,
    campaign_name: str,
    reviewer_name: str,
    comment: Optional[str],
    app_url: str = "https://cx.sieteic.com",
) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    subject = f"✅ Evaluación #{evaluation_id} aprobada — {campaign_name}"
    comment_block = (
        f'<p style="background:#f0fdf4;border-left:4px solid #22c55e;padding:12px 16px;'
        f'border-radius:4px;margin:16px 0;">{comment}</p>'
        if comment else ""
    )
    html = _wrap(f"""
      <h2 style="margin:0 0 8px;color:#16a34a;">¡Tu evaluación fue aprobada!</h2>
      <p style="color:#555;margin:0 0 16px;">Hola <strong>{evaluator_name}</strong>,</p>
      <p>La evaluación <strong>#{evaluation_id}</strong> de la campaña
         <strong>{campaign_name}</strong> fue <strong>aprobada</strong>
         por <em>{reviewer_name}</em>.</p>
      {comment_block}
      <a href="{app_url}/evaluations/{evaluation_id}"
         style="display:inline-block;margin-top:16px;padding:10px 22px;
                background:#16a34a;color:#fff;border-radius:6px;
                text-decoration:none;font-weight:600;">Ver evaluación</a>
    """, "Siete CX — Plataforma de Experiencia del Cliente")
    return subject, html


def email_evaluation_rejected(
    evaluator_name: str,
    evaluation_id: int,
    campaign_name: str,
    reviewer_name: str,
    rejection_type: str,
    requires_revisit: bool,
    comment: Optional[str],
    app_url: str = "https://cx.sieteic.com",
) -> tuple[str, str]:
    subject = f"❌ Evaluación #{evaluation_id} rechazada — {campaign_name}"
    type_label = "Descartada" if rejection_type == "descartado" else "Discrepancia detectada"
    revisit_note = (
        '<p style="background:#fef9c3;border-left:4px solid #eab308;padding:10px 14px;'
        'border-radius:4px;">⚠️ Se requiere <strong>re-visita</strong> a la sucursal.</p>'
        if requires_revisit else ""
    )
    comment_block = (
        f'<p style="background:#fef2f2;border-left:4px solid #ef4444;padding:12px 16px;'
        f'border-radius:4px;margin:16px 0;">{comment}</p>'
        if comment else ""
    )
    html = _wrap(f"""
      <h2 style="margin:0 0 8px;color:#dc2626;">Evaluación rechazada</h2>
      <p style="color:#555;margin:0 0 16px;">Hola <strong>{evaluator_name}</strong>,</p>
      <p>La evaluación <strong>#{evaluation_id}</strong> de la campaña
         <strong>{campaign_name}</strong> fue <strong>rechazada</strong>
         por <em>{reviewer_name}</em>.</p>
      <p><strong>Motivo:</strong> {type_label}</p>
      {revisit_note}
      {comment_block}
      <a href="{app_url}/evaluations/{evaluation_id}"
         style="display:inline-block;margin-top:16px;padding:10px 22px;
                background:#dc2626;color:#fff;border-radius:6px;
                text-decoration:none;font-weight:600;">Ver detalle</a>
    """, "Siete CX — Plataforma de Experiencia del Cliente")
    return subject, html


def email_evaluation_sent_to_edit(
    evaluator_name: str,
    evaluation_id: int,
    campaign_name: str,
    reviewer_name: str,
    comment: Optional[str],
    app_url: str = "https://cx.sieteic.com",
) -> tuple[str, str]:
    subject = f"✏️ Evaluación #{evaluation_id} requiere corrección — {campaign_name}"
    comment_block = (
        f'<p style="background:#eff6ff;border-left:4px solid #3b82f6;padding:12px 16px;'
        f'border-radius:4px;margin:16px 0;"><strong>Indicación del revisor:</strong><br>{comment}</p>'
        if comment else ""
    )
    html = _wrap(f"""
      <h2 style="margin:0 0 8px;color:#2563eb;">Tu evaluación necesita correcciones</h2>
      <p style="color:#555;margin:0 0 16px;">Hola <strong>{evaluator_name}</strong>,</p>
      <p>La evaluación <strong>#{evaluation_id}</strong> de la campaña
         <strong>{campaign_name}</strong> fue devuelta para corrección
         por <em>{reviewer_name}</em>.</p>
      {comment_block}
      <p>Por favor corrígela y reenvíala desde la plataforma.</p>
      <a href="{app_url}/evaluations/{evaluation_id}"
         style="display:inline-block;margin-top:16px;padding:10px 22px;
                background:#2563eb;color:#fff;border-radius:6px;
                text-decoration:none;font-weight:600;">Ir a la evaluación</a>
    """, "Siete CX — Plataforma de Experiencia del Cliente")
    return subject, html


def email_evaluation_ready_for_review(
    reviewer_name: str,
    evaluation_id: int,
    campaign_name: str,
    evaluator_name: str,
    app_url: str = "https://cx.sieteic.com",
) -> tuple[str, str]:
    subject = f"🔔 Evaluación #{evaluation_id} lista para revisión — {campaign_name}"
    html = _wrap(f"""
      <h2 style="margin:0 0 8px;color:#7c3aed;">Evaluación lista para revisión</h2>
      <p style="color:#555;margin:0 0 16px;">Hola <strong>{reviewer_name}</strong>,</p>
      <p>El evaluador <strong>{evaluator_name}</strong> actualizó la evaluación
         <strong>#{evaluation_id}</strong> de la campaña
         <strong>{campaign_name}</strong> y está lista para tu revisión.</p>
      <a href="{app_url}/evaluations/{evaluation_id}"
         style="display:inline-block;margin-top:16px;padding:10px 22px;
                background:#7c3aed;color:#fff;border-radius:6px;
                text-decoration:none;font-weight:600;">Revisar ahora</a>
    """, "Siete CX — Plataforma de Experiencia del Cliente")
    return subject, html
