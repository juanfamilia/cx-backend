"""
Semilla idempotente para probar Siete Field + análisis Dooblo (cuota, respuesta, GPS).

Crea estudio, proyecto ``dooblo``, fuente externa y una política versionada con
``response_quality_enabled`` y ``gps_quality_enabled``, incluyendo un ejemplo de
``gps_column_pairs`` para encuestas donde los nombres de columna no siguen la heurística.

Requisitos:

- Empresa existente con al menos un ``end_clients`` activo (``deleted_at`` null).
- Variables de entorno::

      FIELD_SANDBOX_COMPANY_ID=1          # obligatorio
      FIELD_SANDBOX_CLIENT_ID=             # opcional; si falta, primer cliente de la empresa
      FIELD_SANDBOX_DOOBLO_SURVEY_ID=      # opcional; default ``sandbox-survey``

Ejecutar::

    python -m app.seeder.field_sandbox_seeder

No sobrescribe políticas ya sembradas (nombre ``__FIELD_SANDBOX_POLICY__``).
Para testear el pipeline async dispare una corrida ``field_analysis`` vinculando
``field_policy_set_id`` y credenciales Dooblo de la empresa según su flujo actual.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.field_decision_model import (
    SOURCE_TYPE_DOOBLO,
    FieldPolicySet,
    FieldProjectExternalSource,
)
from app.models.field_project_model import FieldProject
from app.models.field_study_model import FieldStudy
from app.models.end_client_model import EndClient

logger = logging.getLogger(__name__)

SANDBOX_STUDY_NAME = "__FIELD_SANDBOX_STUDY__"
SANDBOX_PROJECT_NAME = "__FIELD_SANDBOX_DOOBLO_PROJECT__"
SANDBOX_POLICY_NAME = "__FIELD_SANDBOX_POLICY__"

SANDBOX_POLICY_CONFIG: dict[str, Any] = {
    "quota_max_deviation_pct": 25,
    "response_quality_enabled": True,
    "gps_quality_enabled": True,
    "dooblo_tabular_max_subjects": 20,
    "interview_duration_seconds_min": 45,
    "interview_duration_seconds_max": 7200,
    "straight_lining_enabled": True,
    "gps_max_internal_distance_km": 75,
    "gps_flag_null_island": True,
    # Ejemplo: ajuste o borre y use solo heurística según su export real.
    "gps_column_pairs": [
        ["CUSTOM_LAT", "CUSTOM_LON"],
        {"lat": "gps_lat", "lon": "gps_lon"},
    ],
}


async def _resolve_client_id(session: AsyncSession, company_id: int) -> int | None:
    raw = os.environ.get("FIELD_SANDBOX_CLIENT_ID", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            logger.error("FIELD_SANDBOX_CLIENT_ID inválido")
            return None
    res = await session.execute(
        select(EndClient.id)
        .where(EndClient.company_id == company_id, EndClient.deleted_at.is_(None))
        .limit(1)
    )
    row = res.scalar_one_or_none()
    return int(row) if row is not None else None


async def _next_policy_version(session: AsyncSession, field_project_id: int) -> int:
    res = await session.execute(
        select(func.coalesce(func.max(FieldPolicySet.version), 0)).where(
            FieldPolicySet.field_project_id == field_project_id
        )
    )
    return int(res.scalar_one()) + 1


async def seed_field_sandbox(session: AsyncSession) -> dict[str, Any]:
    raw_co = os.environ.get("FIELD_SANDBOX_COMPANY_ID", "").strip()
    if not raw_co:
        raise ValueError("Defina FIELD_SANDBOX_COMPANY_ID")
    company_id = int(raw_co)

    client_id = await _resolve_client_id(session, company_id)
    if client_id is None:
        raise ValueError(
            "No hay FIELD_SANDBOX_CLIENT_ID y la empresa no tiene end_clients activos."
        )

    survey_id = os.environ.get("FIELD_SANDBOX_DOOBLO_SURVEY_ID", "sandbox-survey").strip() or "sandbox-survey"

    res_st = await session.execute(
        select(FieldStudy).where(
            FieldStudy.company_id == company_id,
            FieldStudy.client_id == client_id,
            FieldStudy.name == SANDBOX_STUDY_NAME,
        )
    )
    study = res_st.scalar_one_or_none()
    if study is None:
        study = FieldStudy(
            company_id=company_id,
            client_id=client_id,
            name=SANDBOX_STUDY_NAME,
            description="Semilla sandbox Field / Dooblo (no producción).",
            status="draft",
        )
        session.add(study)
        await session.flush()
        logger.info("FieldStudy sandbox creado id=%s", study.id)

    res_pr = await session.execute(
        select(FieldProject).where(
            FieldProject.company_id == company_id,
            FieldProject.client_id == client_id,
            FieldProject.name == SANDBOX_PROJECT_NAME,
            FieldProject.deleted_at.is_(None),
        )
    )
    project = res_pr.scalar_one_or_none()
    if project is None:
        project = FieldProject(
            company_id=company_id,
            client_id=client_id,
            study_id=study.id,
            name=SANDBOX_PROJECT_NAME,
            description="Proyecto sandbox para análisis Dooblo (policy + external source).",
            status="draft",
            ingest_mode="dooblo",
        )
        session.add(project)
        await session.flush()
        logger.info("FieldProject sandbox creado id=%s", project.id)
    elif project.study_id != study.id:
        project.study_id = study.id
        await session.flush()

    res_src = await session.execute(
        select(FieldProjectExternalSource).where(
            FieldProjectExternalSource.field_project_id == project.id,
            FieldProjectExternalSource.source_type == SOURCE_TYPE_DOOBLO,
            FieldProjectExternalSource.external_survey_id == survey_id,
        )
    )
    src = res_src.scalar_one_or_none()
    if src is None:
        src = FieldProjectExternalSource(
            field_project_id=project.id,
            company_id=company_id,
            source_type=SOURCE_TYPE_DOOBLO,
            external_survey_id=survey_id,
            is_active=True,
        )
        session.add(src)
        await session.flush()
        logger.info("FieldProjectExternalSource sandbox creado id=%s", src.id)

    res_po = await session.execute(
        select(FieldPolicySet).where(
            FieldPolicySet.field_project_id == project.id,
            FieldPolicySet.name == SANDBOX_POLICY_NAME,
        )
    )
    policy = res_po.scalar_one_or_none()
    if policy is None:
        ver = await _next_policy_version(session, project.id)
        policy = FieldPolicySet(
            field_project_id=project.id,
            version=ver,
            name=SANDBOX_POLICY_NAME,
            config=SANDBOX_POLICY_CONFIG,
            created_by_user_id=None,
        )
        session.add(policy)
        await session.flush()
        logger.info("FieldPolicySet sandbox creado id=%s version=%s", policy.id, policy.version)

    await session.commit()

    return {
        "company_id": company_id,
        "client_id": client_id,
        "field_study_id": study.id,
        "field_project_id": project.id,
        "field_project_external_source_id": src.id,
        "field_policy_set_id": policy.id,
        "external_survey_id": survey_id,
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    async with AsyncSessionLocal() as session:
        info = await seed_field_sandbox(session)
    print("Field sandbox seed OK:")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print()
    print("Siguiente paso: dispare field_analysis con field_project_id y field_policy_set_id")
    print("anteriores; configure credenciales Dooblo para la empresa y un survey real")


if __name__ == "__main__":
    asyncio.run(main())
