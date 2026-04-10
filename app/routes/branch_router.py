from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.branch_model import (
    BranchCreate,
    BranchImportResult,
    BranchImportRow,
    BranchPublic,
    BranchUpdate,
    BranchesPublic,
)
from app.services.branch_services import (
    bulk_import_branches,
    create_branch,
    delete_branch,
    get_branch,
    get_branches,
    update_branch,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


def _company_id_for_user(request: Request, company_id_param: Optional[int]) -> int:
    user = request.state.user
    if user.role == 0:
        if company_id_param is None:
            raise PermissionDeniedException(
                custom_message="superadmin must provide company_id"
            )
        return company_id_param
    return user.company_id


@router.get("/", response_model=BranchesPublic)
async def list_branches(
    request: Request,
    session: AsyncSession = Depends(get_db),
    company_id: Optional[int] = Query(None),
    zone_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    offset: int = 0,
    limit: int = Query(default=50, le=200),
) -> BranchesPublic:
    cid = _company_id_for_user(request, company_id)
    return await get_branches(session, cid, offset, limit, zone_id, is_active, search)


@router.get("/{branch_id}", response_model=BranchPublic)
async def get_one(
    request: Request,
    branch_id: int,
    session: AsyncSession = Depends(get_db),
) -> BranchPublic:
    branch = await get_branch(session, branch_id)
    user = request.state.user
    if user.role != 0 and branch.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="access this branch")
    return branch


@router.post("/", response_model=BranchPublic, status_code=201)
async def create(
    request: Request,
    payload: BranchCreate,
    session: AsyncSession = Depends(get_db),
) -> BranchPublic:
    user = request.state.user
    if user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create branches")
    if user.role != 0:
        payload.company_id = user.company_id
    return await create_branch(session, payload)


@router.put("/{branch_id}", response_model=BranchPublic)
async def update(
    request: Request,
    branch_id: int,
    payload: BranchUpdate,
    session: AsyncSession = Depends(get_db),
) -> BranchPublic:
    user = request.state.user
    if user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="update branches")
    branch = await get_branch(session, branch_id)
    if user.role != 0 and branch.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="update this branch")
    return await update_branch(session, branch_id, payload)


@router.delete("/{branch_id}", response_model=BranchPublic)
async def delete(
    request: Request,
    branch_id: int,
    session: AsyncSession = Depends(get_db),
) -> BranchPublic:
    user = request.state.user
    if user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="delete branches")
    branch = await get_branch(session, branch_id)
    if user.role != 0 and branch.company_id != user.company_id:
        raise PermissionDeniedException(custom_message="delete this branch")
    return await delete_branch(session, branch_id)


@router.post("/import", response_model=BranchImportResult, status_code=200)
async def bulk_import(
    request: Request,
    rows: list[BranchImportRow],
    company_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_db),
) -> BranchImportResult:
    """
    Importación masiva de sucursales (upsert por código).
    Útil para cargar las 292 oficinas desde Excel/CSV procesado en el cliente.
    """
    user = request.state.user
    if user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="import branches")
    cid = _company_id_for_user(request, company_id)
    return await bulk_import_branches(session, cid, rows)
