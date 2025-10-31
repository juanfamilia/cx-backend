from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.theme_model import (
    CompanyThemeCreate,
    CompanyThemeUpdate,
    CompanyThemePublic,
)
from app.services.theme_services import (
    get_company_theme,
    get_or_create_default_theme,
    create_company_theme,
    update_company_theme,
    get_theme_css,
    preview_theme,
)
from app.utils.deps import check_company_payment_status, get_auth_user
from app.utils.exeptions import PermissionDeniedException


router = APIRouter(
    prefix="/theme",
    tags=["White-Label Theming"],
    dependencies=[Depends(get_auth_user), Depends(check_company_payment_status)],
)


@router.get("/")
async def get_my_company_theme(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> CompanyThemePublic:
    """Get current user's company theme"""
    
    company_id = request.state.user.company_id
    theme = await get_or_create_default_theme(session, company_id)
    
    return theme


@router.post("/")
async def create_theme(
    request: Request,
    theme_data: CompanyThemeCreate,
    session: AsyncSession = Depends(get_db),
) -> CompanyThemePublic:
    """Create company theme (admin only)"""
    
    # Only admins can create themes
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="create themes")
    
    # Ensure creating for own company (unless superadmin)
    if request.state.user.role == 1:
        if theme_data.company_id != request.state.user.company_id:
            raise PermissionDeniedException(custom_message="create themes for other companies")
    
    theme = await create_company_theme(session, theme_data)
    return theme


@router.put("/")
async def update_theme(
    request: Request,
    theme_data: CompanyThemeUpdate,
    session: AsyncSession = Depends(get_db),
) -> CompanyThemePublic:
    """Update company theme (admin only)"""
    
    if request.state.user.role not in [0, 1]:
        raise PermissionDeniedException(custom_message="update themes")
    
    company_id = request.state.user.company_id
    theme = await update_company_theme(session, company_id, theme_data)
    
    return theme


@router.get("/css")
async def get_theme_css_route(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Get generated CSS for company theme"""
    
    company_id = request.state.user.company_id
    css = await get_theme_css(session, company_id)
    
    return Response(content=css, media_type="text/css")


@router.post("/preview")
async def preview_theme_route(
    theme_data: dict,
):
    """Preview theme CSS without saving (for theme editor)"""
    
    css = await preview_theme(theme_data)
    return Response(content=css, media_type="text/css")


@router.get("/public/{company_id}")
async def get_public_theme(
    company_id: int,
    session: AsyncSession = Depends(get_db),
) -> CompanyThemePublic:
    """
    Get public theme information for a company
    (Used for login page branding before authentication)
    """
    
    theme = await get_or_create_default_theme(session, company_id)
    
    # Return limited public info only
    return {
        "company_logo_url": theme.company_logo_url,
        "company_favicon_url": theme.company_favicon_url,
        "company_name_override": theme.company_name_override,
        "primary_color": theme.primary_color,
        "secondary_color": theme.secondary_color,
    }
