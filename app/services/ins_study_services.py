import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.company_model import Company
from app.models.ins_study_model import InsStudy, InsStudyCreate, InsStudyPublic
from app.models.user_model import User
from app.utils.exeptions import PermissionDeniedException

logger = logging.getLogger(__name__)


def _resolve_company_id_for_write(user: User, body: InsStudyCreate) -> int:
    if user.role == 0:
        if body.company_id is None:
            raise PermissionDeniedException(
                custom_message="crear estudio InS: indique company_id"
            )
        return body.company_id
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="crear estudio InS")
    return user.company_id


async def assert_ins_study_company_access(
    session: AsyncSession, study: InsStudy, user: User
) -> None:
    if user.role == 0:
        return
    if user.company_id is None or study.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="acceder a este estudio InS")


async def create_ins_study(
    session: AsyncSession, user: User, body: InsStudyCreate
) -> InsStudyPublic:
    company_id = _resolve_company_id_for_write(user, body)
    company = await session.get(Company, company_id)
    if company is None or company.deleted_at is not None:
        raise PermissionDeniedException(custom_message="empresa inválida")
    if user.role != 0 and not company.siete_ins_enabled:
        raise PermissionDeniedException(
            custom_message="Siete InS no está habilitado para esta empresa"
        )

    row = InsStudy(
        company_id=company_id,
        title=body.title.strip(),
        objective=(body.objective or "").strip() or None,
        created_by=user.id,
        status="draft",
        pipeline_status="idle",
        rubric_version="v0",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    logger.info("ins_study created id=%s company_id=%s", row.id, company_id)
    return InsStudyPublic.model_validate(row)


async def list_ins_studies(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
) -> list[InsStudyPublic]:
    if user.role == 0:
        if company_id is None:
            raise PermissionDeniedException(
                custom_message="listar estudios InS: indique company_id"
            )
        company = await session.get(Company, company_id)
        if company is None or company.deleted_at is not None:
            raise PermissionDeniedException(custom_message="empresa inválida")
        cid = company_id
    else:
        if user.company_id is None:
            return []
        cid = user.company_id
        c = await session.get(Company, cid)
        if c is None or not c.siete_ins_enabled:
            return []

    stmt = (
        select(InsStudy)
        .where(InsStudy.company_id == cid, InsStudy.deleted_at.is_(None))
        .order_by(InsStudy.updated_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [InsStudyPublic.model_validate(r) for r in rows]


async def get_ins_study(
    session: AsyncSession, user: User, study_id: int
) -> InsStudyPublic | None:
    row = await session.get(InsStudy, study_id)
    if row is None or row.deleted_at is not None:
        return None
    await assert_ins_study_company_access(session, row, user)
    return InsStudyPublic.model_validate(row)


async def run_ins_study_pipeline_stub(
    session: AsyncSession, user: User, study_id: int
) -> InsStudyPublic:
    """MVP: marca el pipeline como listo (luego: transcripción + rúbrica + informe)."""
    if user.role not in (0, 1, 2):
        raise PermissionDeniedException(
            custom_message="ejecutar pipeline InS (solo admin o gerente)"
        )
    row = await session.get(InsStudy, study_id)
    if row is None or row.deleted_at is not None:
        raise PermissionDeniedException(custom_message="estudio InS no encontrado")
    await assert_ins_study_company_access(session, row, user)
    if user.role != 0:
        c = await session.get(Company, row.company_id)
        if c is None or not c.siete_ins_enabled:
            raise PermissionDeniedException(
                custom_message="Siete InS no está habilitado para esta empresa"
            )

    row.pipeline_status = "ready"
    row.status = "active"
    session.add(row)
    await session.commit()
    await session.refresh(row)
    logger.info("ins_study pipeline stub OK id=%s", study_id)
    return InsStudyPublic.model_validate(row)
