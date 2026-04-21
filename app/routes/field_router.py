"""
Siete Field — proyectos de control de levantamiento (MVP interno, CSV-ready).

Prefijo: `/api/v1/field`
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import Company
from app.models.field_project_model import (
    FieldImportRunPublic,
    FieldProjectCreate,
    FieldProjectPublic,
)
from app.services.field_import_services import import_field_csv_2026_1
from app.services.field_project_services import create_field_project, list_field_projects
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.field_access import require_field_product_access

router = APIRouter(
    prefix="/field",
    tags=["Siete Field"],
    dependencies=[
        Depends(get_auth_user),
        Depends(check_company_payment_status),
    ],
)


@router.get("/access")
async def field_access_probe(request: Request, session: AsyncSession = Depends(get_db)):
    user = request.state.user
    if user.role == 0:
        return {"field_enabled": True, "scope": "global"}
    if user.company_id is None:
        return {"field_enabled": False, "scope": None}
    c = await session.get(Company, user.company_id)
    ok = c is not None and bool(c.siete_field_enabled)
    return {"field_enabled": ok, "scope": "company", "company_id": user.company_id}


@router.get(
    "/projects",
    response_model=list[FieldProjectPublic],
    dependencies=[Depends(require_field_product_access)],
)
async def list_projects(
    request: Request,
    company_id: Optional[int] = Query(None, description="Rol 0: obligatorio."),
    client_id: Optional[int] = Query(None, description="Filtrar por cliente final."),
    session: AsyncSession = Depends(get_db),
):
    return await list_field_projects(
        session, request.state.user, company_id, client_id
    )


@router.post(
    "/projects",
    response_model=FieldProjectPublic,
    dependencies=[Depends(require_field_product_access)],
)
async def create_project(
    request: Request,
    body: FieldProjectCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_field_project(session, request.state.user, body)


@router.post(
    "/projects/{project_id}/import",
    response_model=FieldImportRunPublic,
    dependencies=[Depends(require_field_product_access)],
    summary="Importar CSV formato 2026.1 (validación + registro de corrida)",
)
async def import_project_csv(
    project_id: int,
    request: Request,
    file: UploadFile = File(..., description="Archivo .csv UTF-8"),
    session: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    run = await import_field_csv_2026_1(session, request.state.user, project_id, raw)
    return FieldImportRunPublic.model_validate(run)
