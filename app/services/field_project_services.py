from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.end_client_model import EndClient
from app.models.field_project_model import (
    FieldProject,
    FieldProjectCreate,
    FieldProjectPatch,
    FieldProjectPublic,
)
from app.models.field_study_model import FieldStudy
from app.models.user_model import User
from app.platform_intelligence.signals_service import emit_platform_signal_safe
from app.utils.exeptions import NotFoundException, PermissionDeniedException


def _company_id_for_write(user: User, body_company_id: Optional[int]) -> int:
    if user.role == 0:
        cid = body_company_id if body_company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="crear proyecto Field: indique company_id"
            )
        return cid
    if user.company_id is None:
        raise PermissionDeniedException(custom_message="sin empresa")
    return user.company_id


async def assert_field_staff(user: User) -> None:
    if user.role not in (0, 1, 2):
        raise PermissionDeniedException(
            custom_message="gestionar Field (solo admin o gerente)"
        )


def _assert_project_company_access(user: User, project: FieldProject) -> None:
    """Misma regla que capa de decisión / import."""
    if user.role == 0:
        return
    if user.company_id is None or project.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="proyecto Field no permitido")


async def _get_field_project_writable(
    session: AsyncSession, project_id: int
) -> FieldProject:
    row = await session.get(FieldProject, project_id)
    if row is None or row.deleted_at is not None:
        raise NotFoundException("Proyecto Field no encontrado")
    return row


async def _assert_client_belongs_to_company(
    session: AsyncSession, client_id: int, company_id: int
) -> None:
    ec = await session.get(EndClient, client_id)
    if ec is None or ec.deleted_at is not None or ec.company_id != company_id:
        raise PermissionDeniedException(custom_message="cliente final inválido")


async def _assert_study_matches_project_client(
    session: AsyncSession, study_id: int, company_id: int, client_id: int
) -> None:
    st = await session.get(FieldStudy, study_id)
    if st is None or st.company_id != company_id or st.client_id != client_id:
        raise PermissionDeniedException(custom_message="estudio Field inválido para este cliente")


async def list_field_projects(
    session: AsyncSession,
    user: User,
    company_id: Optional[int],
    client_id: Optional[int],
) -> list[FieldProjectPublic]:
    await assert_field_staff(user)
    if user.role == 0:
        cid = company_id if company_id is not None else user.company_id
        if cid is None:
            raise PermissionDeniedException(
                custom_message="listar proyectos Field: indique company_id"
            )
    else:
        cid = user.company_id
        if cid is None:
            return []

    stmt = select(FieldProject).where(
        FieldProject.company_id == cid,
        FieldProject.deleted_at.is_(None),
    )
    if client_id is not None:
        stmt = stmt.where(FieldProject.client_id == client_id)
    stmt = stmt.order_by(FieldProject.updated_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [FieldProjectPublic.model_validate(r) for r in rows]


async def create_field_project(
    session: AsyncSession, user: User, body: FieldProjectCreate
) -> FieldProjectPublic:
    await assert_field_staff(user)
    cid = _company_id_for_write(user, body.company_id)
    if user.role != 0 and body.company_id not in (None, user.company_id):
        raise PermissionDeniedException(custom_message="company_id no permitido")

    await _assert_client_belongs_to_company(session, body.client_id, cid)

    if body.study_id is not None:
        await _assert_study_matches_project_client(
            session, body.study_id, cid, body.client_id
        )

    row = FieldProject(
        company_id=cid,
        client_id=body.client_id,
        study_id=body.study_id,
        name=body.name.strip(),
        description=(body.description or "").strip() or None,
        import_format_version="2026.1",
        status="draft",
        ingest_mode=body.ingest_mode,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    await emit_platform_signal_safe(
        session,
        company_id=cid,
        user_id=user.id,
        source_domain="field",
        signal_code="field.project_created",
        summary=f"Field: proyecto «{row.name[:240]}»",
        severity="low",
        payload={
            "field_project_id": row.id,
            "field_study_id": row.study_id,
            "ingest_mode": row.ingest_mode,
            "client_id": row.client_id,
            "status": row.status,
        },
        field_study_id=row.study_id,
        field_project_id=row.id,
    )
    return FieldProjectPublic.model_validate(row)


async def patch_field_project(
    session: AsyncSession,
    user: User,
    project_id: int,
    body: FieldProjectPatch,
) -> FieldProjectPublic:
    await assert_field_staff(user)
    project = await _get_field_project_writable(session, project_id)
    _assert_project_company_access(user, project)

    payload = body.model_dump(exclude_unset=True)
    if not payload:
        return FieldProjectPublic.model_validate(project)

    if "study_id" in payload:
        sid = payload["study_id"]
        if sid is not None:
            await _assert_study_matches_project_client(
                session, sid, project.company_id, project.client_id
            )
        project.study_id = sid

    if "execution_metadata" in payload:
        raw = payload["execution_metadata"]
        base = dict(project.execution_metadata or {})
        if isinstance(raw, dict):
            base.update(raw)
            project.execution_metadata = base
        elif raw is None:
            project.execution_metadata = {}

    await session.commit()
    await session.refresh(project)
    return FieldProjectPublic.model_validate(project)
