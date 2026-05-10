"""Catálogo Framework Library."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import asc, select

from app.models.field_framework_template_model import FieldFrameworkTemplate, FieldFrameworkTemplatePublic
from app.models.user_model import User
from app.services.field_study_services import assert_field_staff

# Alineado a `study_type` en `examples/instrument_spec_v1.schema.json`.
FRAMEWORK_TEMPLATE_STUDY_TYPES = frozenset(
    {
        "cx",
        "ua",
        "brand_tracking",
        "concept_test",
        "mystery_shopper",
        "focus_group",
        "other",
    }
)


async def list_field_framework_templates_for_api(
    session: AsyncSession,
    user: User,
    *,
    study_type: Optional[str] = None,
) -> list[FieldFrameworkTemplatePublic]:
    await assert_field_staff(user)
    stmt = select(FieldFrameworkTemplate).where(FieldFrameworkTemplate.is_active.is_(True))
    if study_type is not None:
        stmt = stmt.where(FieldFrameworkTemplate.study_type == study_type.strip().lower())
    stmt = stmt.order_by(asc(FieldFrameworkTemplate.sort_order), asc(FieldFrameworkTemplate.title))
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldFrameworkTemplatePublic.model_validate(r) for r in rows]


async def get_field_framework_template_by_slug_version(
    session: AsyncSession,
    slug: str,
    framework_version: str,
) -> FieldFrameworkTemplate | None:
    stmt = select(FieldFrameworkTemplate).where(
        FieldFrameworkTemplate.slug == slug.strip(),
        FieldFrameworkTemplate.framework_version == framework_version.strip(),
        FieldFrameworkTemplate.is_active.is_(True),
    )
    return (await session.execute(stmt)).scalars().first()
