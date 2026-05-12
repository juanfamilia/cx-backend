"""Persistencia de corridas Auto QA bootstrap (`instrument_qa_runtime`)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc
from sqlmodel import select

from app.models.field_instrument_revision_model import FieldInstrumentRevision
from app.models.field_instrument_qa_run_model import (
    FieldInstrumentQARun,
    FieldInstrumentQARunPublic,
    InstrumentQAFindingPublic,
    InstrumentQAExecuteResponse,
)
from app.models.user_model import User
from app.services.field_instrument_revision_services import (
    _effective_company_id,
    _get_revision_writable,
)
from app.services.field_study_services import assert_field_staff
from app.services.instrument_qa_rules_v1 import (
    QA_RULESET_BOOTSTRAP_V1,
    QA_SOURCE,
    run_instrument_qa_rules_bootstrap,
    summarize_qa_severities,
)
from app.services.instrument_spec_validate import compute_instrument_spec_content_hash


async def execute_instrument_qa_bootstrap_run(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
) -> InstrumentQAExecuteResponse:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    rev = await _get_revision_writable(session, revision_id, cid)

    if rev.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="solo revisiones en borrador admiten nueva corrida QA",
        )

    spec: dict[str, Any] = dict(rev.spec_json) if isinstance(rev.spec_json, dict) else {}
    content_hash = compute_instrument_spec_content_hash(spec)

    raw_findings = run_instrument_qa_rules_bootstrap(spec)
    stops, fix_now, monitor = summarize_qa_severities(raw_findings)
    payload = [f.to_json_dict() for f in raw_findings]

    row = FieldInstrumentQARun(
        revision_id=revision_id,
        company_id=cid,
        ruleset_version=QA_RULESET_BOOTSTRAP_V1,
        source=QA_SOURCE,
        content_hash=content_hash,
        findings_json=payload,
        stop_count=stops,
        fix_now_count=fix_now,
        monitor_count=monitor,
        created_by_user_id=user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    rev_row = await session.get(FieldInstrumentRevision, revision_id)
    if rev_row is not None:
        rev_row.last_ruleset_version = QA_RULESET_BOOTSTRAP_V1
        await session.commit()
        await session.refresh(rev_row)

    findings_pub = [
        InstrumentQAFindingPublic(
            rule_id=f.rule_id,
            severity=f.severity,
            item_id=f.item_id,
            block_id=f.block_id,
            message=f.message,
        )
        for f in raw_findings
    ]

    return InstrumentQAExecuteResponse(
        run=FieldInstrumentQARunPublic.model_validate(row),
        findings=findings_pub,
    )


async def list_instrument_qa_runs(
    session: AsyncSession,
    user: User,
    revision_id: int,
    company_id: Optional[int],
    *,
    limit: int = 20,
) -> list[FieldInstrumentQARunPublic]:
    await assert_field_staff(user)
    cid = _effective_company_id(user, company_id)
    await _get_revision_writable(session, revision_id, cid)

    lim = max(1, min(limit, 100))
    stmt = (
        select(FieldInstrumentQARun)
        .where(
            FieldInstrumentQARun.revision_id == revision_id,
            FieldInstrumentQARun.company_id == cid,
        )
        .order_by(desc(FieldInstrumentQARun.created_at))
        .limit(lim)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldInstrumentQARunPublic.model_validate(r) for r in rows]
