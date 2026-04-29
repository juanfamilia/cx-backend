"""Persistencia y resolución de credenciales Dooblo por empresa."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool  # not needed if sync crypto

from app.core.dooblo_crypto import decrypt_secret, encrypt_secret
from app.integrations.dooblo_client import DoobloCreds, canonical_dooblo_base_url, creds_from_settings
from app.models.company_dooblo_model import CompanyDoobloSettings, DEFAULT_DOOBLO_BASE_URL
from app.models.company_model import Company
from app.models.user_model import User
from app.utils.exeptions import NotFoundException, PermissionDeniedException
from app.services.field_project_services import assert_field_staff
from fastapi import HTTPException


def _naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_dooblo_creds_for_company(
    session: AsyncSession, company_id: int
) -> DoobloCreds | None:
    """
    Prioridad: fila en `company_dooblo_settings` con user + password válidos;
    si no, credenciales globales en `DOOBLO_*` (Railway) si existen.
    """
    res = await session.execute(
        select(CompanyDoobloSettings).where(CompanyDoobloSettings.company_id == company_id)
    )
    row = res.scalars().first()
    if row and row.api_user and row.api_user.strip() and row.password_ciphertext and row.password_ciphertext.strip():
        try:
            password = await run_in_threadpool(decrypt_secret, row.password_ciphertext)
        except ValueError:
            return creds_from_settings()
        base = canonical_dooblo_base_url((row.base_url or "").strip() or DEFAULT_DOOBLO_BASE_URL)
        return DoobloCreds(
            base_url=base,
            user=row.api_user.strip(),
            password=password,
        )
    return creds_from_settings()


def _company_row_usable(row: CompanyDoobloSettings | None) -> bool:
    return bool(
        row
        and (row.api_user or "").strip()
        and (row.password_ciphertext or "").strip()
    )


async def _company_ciphertext_decrypts(row: CompanyDoobloSettings | None) -> bool:
    if not _company_row_usable(row) or row is None or not row.password_ciphertext:
        return False
    try:
        await run_in_threadpool(decrypt_secret, row.password_ciphertext)
    except ValueError:
        return False
    return True


async def get_dooblo_settings_row(
    session: AsyncSession, company_id: int
) -> CompanyDoobloSettings | None:
    r = await session.execute(
        select(CompanyDoobloSettings).where(CompanyDoobloSettings.company_id == company_id)
    )
    return r.scalars().first()


def _assert_company_field_enabled(company: Company) -> None:
    if not company.siete_field_enabled:
        raise HTTPException(400, "Siete Field no está activado para esta empresa.")


async def get_dooblo_settings_public(
    session: AsyncSession, user: User, company_id: int
) -> dict[str, Any]:
    await assert_field_staff(user)
    company = await session.get(Company, company_id)
    if company is None:
        raise NotFoundException("Empresa no encontrada")
    if user.role != 0 and user.company_id != company_id:
        raise PermissionDeniedException(custom_message="Solo su empresa o rol global.")
    _assert_company_field_enabled(company)
    row = await get_dooblo_settings_row(session, company_id)
    has_pw = bool(row and row.password_ciphertext and row.password_ciphertext.strip())
    creds = await get_dooblo_creds_for_company(session, company_id)
    if _company_row_usable(row) and await _company_ciphertext_decrypts(row):
        source = "company"
    elif creds is not None:
        source = "env"
    else:
        source = "none"
    return {
        "company_id": company_id,
        "configured": creds is not None,
        "source": source,
        "base_url": (row.base_url or DEFAULT_DOOBLO_BASE_URL) if row else DEFAULT_DOOBLO_BASE_URL,
        "api_user": (row.api_user or None) if row else None,
        "has_password": has_pw,
        "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
    }


async def upsert_dooblo_settings(
    session: AsyncSession,
    user: User,
    company_id: int,
    *,
    base_url: str | None,
    api_user: str | None,
    password: str | None,
) -> dict[str, Any]:
    await assert_field_staff(user)
    company = await session.get(Company, company_id)
    if company is None:
        raise NotFoundException("Empresa no encontrada")
    if user.role != 0 and user.company_id != company_id:
        raise PermissionDeniedException()
    _assert_company_field_enabled(company)

    row = await get_dooblo_settings_row(session, company_id)
    b = canonical_dooblo_base_url((base_url or "").strip() or DEFAULT_DOOBLO_BASE_URL)
    u = (api_user or "").strip()
    p_in = (password or "").strip()

    if not u:
        raise HTTPException(400, "Indique el usuario o REST_KEY de la API (campo `api_user`).")
    if not p_in and (row is None or not (row.password_ciphertext or "").strip()):
        raise HTTPException(400, "Indique la contraseña o clave de la API (campo `password`).")

    if row is None:
        row = CompanyDoobloSettings(company_id=company_id, base_url=b, api_user=u)
        row.password_ciphertext = await run_in_threadpool(encrypt_secret, p_in)
        session.add(row)
    else:
        row.base_url = b
        row.api_user = u
        if p_in:
            row.password_ciphertext = await run_in_threadpool(encrypt_secret, p_in)
        row.updated_at = _naive_utc()
    await session.commit()
    await session.refresh(row)
    return {
        "company_id": company_id,
        "ok": True,
        "source": "company",
        "base_url": row.base_url,
        "api_user": row.api_user,
        "has_password": bool(row.password_ciphertext),
    }
