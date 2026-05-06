"""Credenciales Qualtrics por empresa (Field), alineado a ``company_dooblo_service``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.dooblo_crypto import decrypt_secret, encrypt_secret
from app.integrations.qualtrics_client import (
    QualtricsCreds,
    canonical_qualtrics_base_url,
    verify_qualtrics_credentials,
)
from app.models.company_model import Company
from app.models.company_qualtrics_model import CompanyQualtricsSettings
from app.models.user_model import User
from app.services.field_project_services import assert_field_staff
from app.utils.exeptions import NotFoundException, PermissionDeniedException
from fastapi import HTTPException


def _naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_qualtrics_creds_for_company(
    session: AsyncSession, company_id: int
) -> QualtricsCreds | None:
    res = await session.execute(
        select(CompanyQualtricsSettings).where(
            CompanyQualtricsSettings.company_id == company_id
        )
    )
    row = res.scalars().first()
    if (
        not row
        or not (row.base_url or "").strip()
        or not row.api_token_ciphertext
        or not row.api_token_ciphertext.strip()
    ):
        return None
    try:
        token = await run_in_threadpool(decrypt_secret, row.api_token_ciphertext)
    except ValueError:
        return None
    try:
        base = canonical_qualtrics_base_url(row.base_url)
    except ValueError:
        return None
    return QualtricsCreds(base_url=base, api_token=token)


async def get_qualtrics_settings_row(
    session: AsyncSession, company_id: int
) -> CompanyQualtricsSettings | None:
    r = await session.execute(
        select(CompanyQualtricsSettings).where(
            CompanyQualtricsSettings.company_id == company_id
        )
    )
    return r.scalars().first()


def _assert_company_field_enabled(company: Company) -> None:
    if not company.siete_field_enabled:
        raise HTTPException(400, "Siete Field no está activado para esta empresa.")


async def get_qualtrics_settings_public(
    session: AsyncSession,
    user: User,
    company_id: int,
    *,
    probe_remote: bool = False,
) -> dict[str, Any]:
    await assert_field_staff(user)
    company = await session.get(Company, company_id)
    if company is None:
        raise NotFoundException("Empresa no encontrada")
    if user.role != 0 and user.company_id != company_id:
        raise PermissionDeniedException(custom_message="Solo su empresa o rol global.")
    _assert_company_field_enabled(company)

    row = await get_qualtrics_settings_row(session, company_id)
    creds = await get_qualtrics_creds_for_company(session, company_id)
    configured = creds is not None

    out: dict[str, Any] = {
        "company_id": company_id,
        "configured": configured,
        "qualtrics_configured": configured,
        "base_url": row.base_url if row else None,
        "has_api_token": bool(row and row.api_token_ciphertext),
        "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
        "api_probe_ok": None,
        "api_probe_status": None,
        "api_probe_error": None,
    }

    if probe_remote and creds is not None:
        ok, status, err = await verify_qualtrics_credentials(creds)
        out["api_probe_ok"] = ok
        out["api_probe_status"] = status
        out["api_probe_error"] = err

    return out


async def upsert_qualtrics_settings(
    session: AsyncSession,
    user: User,
    company_id: int,
    *,
    base_url: str | None,
    api_token: str | None,
) -> dict[str, Any]:
    await assert_field_staff(user)
    company = await session.get(Company, company_id)
    if company is None:
        raise NotFoundException("Empresa no encontrada")
    if user.role != 0 and user.company_id != company_id:
        raise PermissionDeniedException()
    _assert_company_field_enabled(company)

    row = await get_qualtrics_settings_row(session, company_id)
    b_raw = (base_url or "").strip()
    t_in = (api_token or "").strip()

    if not b_raw and row is None:
        raise HTTPException(400, "Indique base_url (datacenter Qualtrics, https://…qualtrics.com).")
    if b_raw:
        try:
            b = canonical_qualtrics_base_url(b_raw)
        except ValueError as e:
            raise HTTPException(400, detail=str(e)) from e
    elif row:
        b = row.base_url
    else:
        b = ""

    if not t_in and (row is None or not (row.api_token_ciphertext or "").strip()):
        raise HTTPException(400, "Indique api_token (una vez guardado puede omitirse al actualizar solo base_url).")

    if row is None:
        row = CompanyQualtricsSettings(company_id=company_id, base_url=b)
        row.api_token_ciphertext = await run_in_threadpool(encrypt_secret, t_in)
        session.add(row)
    else:
        if b_raw:
            row.base_url = b
        if t_in:
            row.api_token_ciphertext = await run_in_threadpool(encrypt_secret, t_in)
        row.updated_at = _naive_utc()
    await session.commit()
    await session.refresh(row)
    return {
        "company_id": company_id,
        "ok": True,
        "base_url": row.base_url,
        "has_api_token": bool(row.api_token_ciphertext),
    }
