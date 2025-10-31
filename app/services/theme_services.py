from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.theme_model import (
    CompanyTheme,
    CompanyThemeCreate,
    CompanyThemeUpdate,
    CompanyThemePublic,
    DEFAULT_THEME,
    generate_theme_css,
)
from app.utils.exeptions import NotFoundException


async def get_company_theme(
    session: AsyncSession,
    company_id: int
) -> CompanyThemePublic:
    """Get theme for a company"""
    
    query = select(CompanyTheme).where(
        CompanyTheme.company_id == company_id,
        CompanyTheme.is_active == True
    )
    result = await session.execute(query)
    theme = result.scalars().first()
    
    if not theme:
        raise NotFoundException("Company theme not found")
    
    return theme


async def get_or_create_default_theme(
    session: AsyncSession,
    company_id: int
) -> CompanyThemePublic:
    """Get existing theme or create default"""
    
    try:
        return await get_company_theme(session, company_id)
    except NotFoundException:
        # Create default theme
        theme_data = CompanyThemeCreate(
            company_id=company_id,
            **DEFAULT_THEME
        )
        return await create_company_theme(session, theme_data)


async def create_company_theme(
    session: AsyncSession,
    theme_data: CompanyThemeCreate
) -> CompanyThemePublic:
    """Create a new company theme"""
    
    # Check if theme already exists
    existing_query = select(CompanyTheme).where(
        CompanyTheme.company_id == theme_data.company_id
    )
    existing_result = await session.execute(existing_query)
    existing_theme = existing_result.scalars().first()
    
    if existing_theme:
        raise ValueError("Theme already exists for this company. Use update instead.")
    
    db_theme = CompanyTheme(**theme_data.model_dump())
    session.add(db_theme)
    await session.commit()
    await session.refresh(db_theme)
    
    return db_theme


async def update_company_theme(
    session: AsyncSession,
    company_id: int,
    theme_data: CompanyThemeUpdate
) -> CompanyThemePublic:
    """Update existing company theme"""
    
    db_theme = await get_company_theme(session, company_id)
    
    update_data = theme_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_theme, key, value)
    
    session.add(db_theme)
    await session.commit()
    await session.refresh(db_theme)
    
    return db_theme


async def get_theme_css(
    session: AsyncSession,
    company_id: int
) -> str:
    """Get generated CSS for a company theme"""
    
    theme = await get_or_create_default_theme(session, company_id)
    return generate_theme_css(theme)


async def preview_theme(theme_data: dict) -> str:
    """
    Generate preview CSS from theme data (without saving)
    Used for theme editor preview
    """
    
    # Create temporary theme object
    from pydantic import BaseModel
    
    class TempTheme(BaseModel):
        primary_color: str = "#8b5cf6"
        secondary_color: str = "#3b82f6"
        accent_color: str = "#10b981"
        success_color: str = "#10b981"
        warning_color: str = "#f59e0b"
        error_color: str = "#ef4444"
        font_family_primary: str = "Inter, system-ui, sans-serif"
        font_family_secondary: str | None = None
        sidebar_background: str = "#1f2937"
        header_background: str = "#ffffff"
        custom_css: str | None = None
    
    temp_theme = TempTheme(**theme_data)
    return generate_theme_css(temp_theme)
