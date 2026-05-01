"""Field: surveys canónicos + métricas KPI (MVP ejecutable)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field_decision_model import (
    SOURCE_TYPE_DOOBLO,
    FieldOperationalSnapshot,
    FieldProjectExternalSource,
)
from app.models.field_execution_model import (
    FieldMetric,
    FieldMetricPublic,
    FieldProjectSyncResponse,
    FieldSurvey,
    FieldSurveyPublic,
)
from app.models.field_project_model import FieldProject
from app.models.user_model import User
from app.services.field_project_services import (
    _assert_project_company_access,
    _get_field_project_writable,
    assert_field_staff,
)


def _utc_naive():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


async def list_project_surveys(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldSurveyPublic]:
    await assert_field_staff(user)
    project = await _get_field_project_writable(session, project_id)
    _assert_project_company_access(user, project)
    res = await session.execute(
        select(FieldSurvey)
        .where(FieldSurvey.field_project_id == project_id)
        .order_by(FieldSurvey.external_survey_id)
    )
    rows = res.scalars().all()
    return [FieldSurveyPublic.model_validate(r) for r in rows]


async def list_project_kpis(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> list[FieldMetricPublic]:
    await assert_field_staff(user)
    project = await _get_field_project_writable(session, project_id)
    _assert_project_company_access(user, project)
    res = await session.execute(
        select(FieldMetric)
        .where(FieldMetric.field_project_id == project_id)
        .order_by(FieldMetric.calculated_at.desc())
    )
    rows = list(res.scalars().all())
    latest_by_code: dict[str, FieldMetric] = {}
    for m in rows:
        if m.metric_code not in latest_by_code:
            latest_by_code[m.metric_code] = m
    return [FieldMetricPublic.model_validate(v) for _, v in sorted(latest_by_code.items())]


def _sample_target(project: FieldProject) -> float:
    meta = project.execution_metadata or {}
    try:
        v = float(meta.get("sample_target", 100))
    except (TypeError, ValueError):
        v = 100.0
    return max(1.0, v)


async def _snapshot_proxy_completed(session: AsyncSession, project_id: int) -> int:
    res = await session.execute(select(FieldOperationalSnapshot).where(FieldOperationalSnapshot.field_project_id == project_id))
    snap = res.scalars().first()
    if snap is None or not snap.quotas_state:
        return 0
    rq = snap.quotas_state.get("response_quality")
    if not isinstance(rq, dict):
        return 0
    summary = rq.get("summary")
    if not isinstance(summary, dict):
        return 0
    try:
        return int(summary.get("row_count") or 0)
    except (TypeError, ValueError):
        return 0


async def sync_field_project_from_sources(
    session: AsyncSession,
    user: User,
    project_id: int,
) -> FieldProjectSyncResponse:
    """
    Stub de sync: materializa FieldSurvey desde fuentes Dooblo activas sin llamar a toda la organización.
    Escribe un punto FieldMetric ``completion_rate`` (proxy MVP desde último snapshot tabular).
    """
    await assert_field_staff(user)
    project = await _get_field_project_writable(session, project_id)
    _assert_project_company_access(user, project)

    partial_errors: list[dict[str, Any]] = []
    upserted = 0

    res = await session.execute(
        select(FieldProjectExternalSource).where(
            FieldProjectExternalSource.field_project_id == project.id,
            FieldProjectExternalSource.is_active,
            FieldProjectExternalSource.source_type == SOURCE_TYPE_DOOBLO,
        )
    )
    sources = list(res.scalars().all())

    for src in sources:
        sid = (src.external_survey_id or "").strip()
        if not sid:
            partial_errors.append(
                {
                    "field_project_external_source_id": src.id,
                    "error": "external_survey_id vacío",
                }
            )
            continue
        try:
            q = await session.execute(
                select(FieldSurvey).where(
                    FieldSurvey.field_project_id == project.id,
                    FieldSurvey.external_survey_id == sid,
                )
            )
            existing = q.scalar_one_or_none()
            display_name = src.wave_id.strip() if src.wave_id and str(src.wave_id).strip() else None
            label = display_name or f"Survey {sid}"
            if existing is None:
                session.add(
                    FieldSurvey(
                        field_project_id=project.id,
                        company_id=project.company_id,
                        external_survey_id=sid,
                        name=label,
                        status="active",
                        survey_metadata={
                            "source_external_id": src.id,
                            "external_project_id": src.external_project_id,
                            "external_customer_id": src.external_customer_id,
                        },
                    )
                )
                upserted += 1
            else:
                meta = dict(existing.survey_metadata or {})
                meta.update(
                    {
                        "source_external_id": src.id,
                        "external_project_id": src.external_project_id,
                        "external_customer_id": src.external_customer_id,
                    }
                )
                existing.survey_metadata = meta
                if not existing.name:
                    existing.name = label
                upserted += 1
        except Exception as exc:  # noqa: BLE001 — partial success por fuente
            partial_errors.append(
                {
                    "field_project_external_source_id": src.id,
                    "external_survey_id": sid,
                    "error": str(exc)[:500],
                }
            )

    project.last_execution_sync_at = _utc_naive()
    session.add(project)

    target = _sample_target(project)
    completed_proxy = await _snapshot_proxy_completed(session, project.id)
    rate = min(1.0, completed_proxy / target)
    session.add(
        FieldMetric(
            field_project_id=project.id,
            metric_code="completion_rate",
            value=rate,
            dimensions={
                "note": "MVP proxy: row_count del último snapshot tabular / sample_target",
                "completed_proxy": completed_proxy,
                "sample_target": int(target),
            },
        )
    )
    metrics_emitted = ["completion_rate"]

    await session.commit()

    return FieldProjectSyncResponse(
        field_project_id=project.id,
        surveys_upserted=upserted,
        metrics_emitted=metrics_emitted,
        partial_errors=partial_errors,
    )
