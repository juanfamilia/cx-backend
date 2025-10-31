from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.dashboard_config_model import (
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigPublic,
    DashboardConfigsPublic,
    WidgetDefinitionsPublic,
)
from app.services.dashboard_config_services import (
    get_user_dashboard_configs,
    get_default_dashboard_config,
    get_dashboard_config_by_id,
    create_dashboard_config,
    update_dashboard_config,
    soft_delete_dashboard_config,
    get_available_widgets,
    get_default_layout_for_role,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/dashboard-config",
    tags=["Dashboard Configuration"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_my_dashboard_configs(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> DashboardConfigsPublic:
    """Get all dashboard configurations for the current user"""
    configs = await get_user_dashboard_configs(session, request.state.user.id)
    return configs


@router.get("/default")
async def get_my_default_config(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> DashboardConfigPublic | dict:
    """Get the default dashboard configuration for the current user"""
    config = await get_default_dashboard_config(session, request.state.user.id)
    
    # If no default config exists, return role-based default layout
    if not config:
        default_layout = get_default_layout_for_role(request.state.user.role)
        return {
            "id": None,
            "user_id": request.state.user.id,
            "config_name": "Default Layout",
            "layout_config": default_layout,
            "is_default": True
        }
    
    return config


@router.get("/{config_id}")
async def get_dashboard_config(
    request: Request,
    config_id: int,
    session: AsyncSession = Depends(get_db),
) -> DashboardConfigPublic:
    """Get a specific dashboard configuration"""
    config = await get_dashboard_config_by_id(session, config_id)
    
    # Check ownership
    if config.user_id != request.state.user.id:
        raise PermissionDeniedException(custom_message="access this dashboard configuration")
    
    return config


@router.post("/")
async def create_new_dashboard_config(
    request: Request,
    config_data: DashboardConfigCreate,
    session: AsyncSession = Depends(get_db),
) -> DashboardConfigPublic:
    """Create a new dashboard configuration"""
    
    # Ensure user can only create configs for themselves
    if config_data.user_id != request.state.user.id:
        raise PermissionDeniedException(custom_message="create configs for other users")
    
    config = await create_dashboard_config(session, config_data)
    return config


@router.put("/{config_id}")
async def update_dashboard_config_route(
    request: Request,
    config_id: int,
    config_data: DashboardConfigUpdate,
    session: AsyncSession = Depends(get_db),
) -> DashboardConfigPublic:
    """Update a dashboard configuration"""
    
    # Check ownership
    db_config = await get_dashboard_config_by_id(session, config_id)
    if db_config.user_id != request.state.user.id:
        raise PermissionDeniedException(custom_message="update this configuration")
    
    config = await update_dashboard_config(session, config_id, config_data)
    return config


@router.delete("/{config_id}")
async def delete_dashboard_config(
    request: Request,
    config_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Soft delete a dashboard configuration"""
    
    # Check ownership
    db_config = await get_dashboard_config_by_id(session, config_id)
    if db_config.user_id != request.state.user.id:
        raise PermissionDeniedException(custom_message="delete this configuration")
    
    await soft_delete_dashboard_config(session, config_id)
    return {"message": "Dashboard configuration deleted successfully"}


@router.get("/widgets/available")
async def get_available_widgets_route(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> WidgetDefinitionsPublic:
    """Get all available widgets for the current user's role"""
    widgets = await get_available_widgets(session, role=request.state.user.role)
    return widgets
