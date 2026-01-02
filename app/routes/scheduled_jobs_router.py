"""
Scheduled Jobs Router
Endpoints for cron jobs and scheduled tasks
Protected by API key for Railway Cron Jobs
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.db import get_db
from shared.core.config import settings
from shared.services.scheduled_reports_services import scheduled_reports_service

router = APIRouter(
    prefix="/jobs",
    tags=["Scheduled Jobs"],
)


async def verify_cron_secret(x_cron_secret: str | None = Header(default=None)):
    """
    Verify the cron job secret key sent by Railway Cron Jobs.
    """
    # 1️⃣ Validar configuración
    if not settings.CRON_SECRET:
        raise HTTPException(
            status_code=500,
            detail="CRON_SECRET not configured"
        )

    # 2️⃣ Validar header presente
    if not x_cron_secret:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Cron-Secret header"
        )

    # 3️⃣ Validar secreto
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid cron secret"
        )

    return True


@router.post("/weekly-digest", summary="Send weekly digest to all companies")
async def trigger_weekly_digest(
    session: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_cron_secret),
):
    """
    Trigger weekly digest emails for all companies.
    Should be called by Railway Cron Job every Monday at 8:00 AM.

    Requires X-Cron-Secret header for authentication.
    """
    result = await scheduled_reports_service.send_all_companies_digest(session)

    return {
        "status": "completed",
        "companies_processed": result["companies_processed"],
        "emails_sent": result["emails_sent"],
        "errors": result["errors"] or None,
    }


@router.post(
    "/weekly-digest/{company_id}",
    summary="Send weekly digest to specific company",
)
async def trigger_company_digest(
    company_id: int,
    session: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_cron_secret),
):
    """
    Trigger weekly digest email for a specific company.
    """
    sent_count = await scheduled_reports_service.send_weekly_digest_email(
        session,
        company_id,
    )

    return {
        "status": "completed",
        "company_id": company_id,
        "emails_sent": sent_count,
    }


@router.get("/health", summary="Health check for cron service")
async def cron_health():
    """Simple health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "scheduled-jobs",
    }
