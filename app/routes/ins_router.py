"""
Siete InS — API del producto de investigación cualitativa (MVP).

Prefijo: `/api/v1/ins` (mismo `API_URL` que CX).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.company_model import Company
from app.models.ins_study_model import InsStudyCreate, InsStudyPublic
from app.services.ins_study_services import (
    create_ins_study,
    get_ins_study,
    list_ins_studies,
    run_ins_study_pipeline_stub,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.ins_access import require_ins_product_access

router = APIRouter(
    prefix="/ins",
    tags=["Siete InS"],
    dependencies=[
        Depends(get_auth_user),
        Depends(check_company_payment_status),
    ],
)


@router.get("/access", summary="Comprobar si la empresa tiene InS activo")
async def ins_access_probe(request: Request, session: AsyncSession = Depends(get_db)):
    """Útil para el front: mismo criterio que `require_ins_product_access`."""
    user = request.state.user
    if user.role == 0:
        return {"ins_enabled": True, "scope": "global"}
    if user.company_id is None:
        return {"ins_enabled": False, "scope": None}
    c = await session.get(Company, user.company_id)
    ok = c is not None and bool(c.siete_ins_enabled)
    return {"ins_enabled": ok, "scope": "company", "company_id": user.company_id}


@router.get(
    "/studies",
    response_model=list[InsStudyPublic],
    # Sin `require_ins_product_access`: si el producto está apagado, el servicio devuelve [] (evita 403 en el listado).
)
async def list_studies(
    request: Request,
    company_id: Optional[int] = Query(
        None,
        description="Rol 0: obligatorio para filtrar por empresa.",
    ),
    session: AsyncSession = Depends(get_db),
):
    return await list_ins_studies(session, request.state.user, company_id)


@router.post(
    "/studies",
    response_model=InsStudyPublic,
    dependencies=[Depends(require_ins_product_access)],
)
async def create_study(
    request: Request,
    body: InsStudyCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_ins_study(session, request.state.user, body)


@router.get(
    "/studies/{study_id}",
    response_model=InsStudyPublic,
    dependencies=[Depends(require_ins_product_access)],
)
async def get_study(
    request: Request,
    study_id: int,
    session: AsyncSession = Depends(get_db),
):
    row = await get_ins_study(session, request.state.user, study_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Estudio InS no encontrado"
        )
    return row


@router.post(
    "/studies/{study_id}/run",
    response_model=InsStudyPublic,
    dependencies=[Depends(require_ins_product_access)],
)
async def run_study_pipeline(
    request: Request,
    study_id: int,
    session: AsyncSession = Depends(get_db),
):
    """
    MVP: marca `pipeline_status=ready` (sin transcripción aún).
    Siguiente iteración: cola → Stream/R2 → Whisper → rúbrica → informe.
    """
    return await run_ins_study_pipeline_stub(session, request.state.user, study_id)
