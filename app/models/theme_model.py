from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.company_model import Company


class CompanyThemeBase(SQLModel):
    """Base model for company white-label theming"""
    company_id: int = Field(foreign_key="companies.id", unique=True)
    
    # Brand Identity
    company_logo_url: str | None = Field(default=None, description="URL to company logo")
    company_favicon_url: str | None = Field(default=None, description="URL to favicon")
    company_name_override: str | None = Field(default=None, description="Custom platform name")
    
    # Color Palette
    primary_color: str = Field(default="#8b5cf6", description="Primary brand color (hex)")
    secondary_color: str = Field(default="#3b82f6", description="Secondary color (hex)")
    accent_color: str = Field(default="#10b981", description="Accent color (hex)")
    success_color: str = Field(default="#10b981", description="Success state color")
    warning_color: str = Field(default="#f59e0b", description="Warning state color")
    error_color: str = Field(default="#ef4444", description="Error state color")
    
    # Typography
    font_family_primary: str = Field(
        default="Inter, system-ui, sans-serif",
        description="Primary font family"
    )
    font_family_secondary: str | None = Field(
        default=None,
        description="Secondary font family (headings)"
    )
    
    # Layout
    sidebar_background: str = Field(default="#1f2937", description="Sidebar background color")
    header_background: str = Field(default="#ffffff", description="Header background color")
    
    # Custom CSS
    custom_css: str | None = Field(
        default=None,
        description="Custom CSS overrides"
    )
    
    # Features Toggle
    features_config: dict | None = Field(
        default=None,
        sa_column_kwargs={"type_": "JSONB"},
        description="Feature flags and custom config"
    )
    
    is_active: bool = Field(default=True, description="Whether theme is active")


class CompanyThemeCreate(CompanyThemeBase):
    """Schema for creating company theme"""
    pass


class CompanyThemeUpdate(SQLModel):
    """Schema for updating company theme"""
    company_logo_url: str | None = None
    company_favicon_url: str | None = None
    company_name_override: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    success_color: str | None = None
    warning_color: str | None = None
    error_color: str | None = None
    font_family_primary: str | None = None
    font_family_secondary: str | None = None
    sidebar_background: str | None = None
    header_background: str | None = None
    custom_css: str | None = None
    features_config: dict | None = None
    is_active: bool | None = None


class CompanyTheme(CompanyThemeBase, table=True):
    """Database table for company themes"""
    __tablename__ = "company_themes"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    
    company: "Company" = Relationship(
        back_populates="theme", sa_relationship_kwargs={"lazy": "noload"}
    )


class CompanyThemePublic(CompanyThemeBase):
    """Public schema for company theme"""
    id: int
    created_at: datetime
    updated_at: datetime


# CSS Generator Helper
def generate_theme_css(theme: CompanyThemePublic) -> str:
    """
    Generate CSS variables from theme configuration
    
    Returns CSS that can be injected into the Angular app
    """
    
    css = f"""
:root {{
    /* Brand Colors */
    --color-primary: {theme.primary_color};
    --color-secondary: {theme.secondary_color};
    --color-accent: {theme.accent_color};
    --color-success: {theme.success_color};
    --color-warning: {theme.warning_color};
    --color-error: {theme.error_color};
    
    /* Typography */
    --font-primary: {theme.font_family_primary};
    --font-secondary: {theme.font_family_secondary or theme.font_family_primary};
    
    /* Layout */
    --sidebar-bg: {theme.sidebar_background};
    --header-bg: {theme.header_background};
}}

/* Apply primary color to key elements */
.btn-primary {{
    background-color: var(--color-primary);
    border-color: var(--color-primary);
}}

.btn-primary:hover {{
    background-color: color-mix(in srgb, var(--color-primary) 85%, black);
}}

.text-primary {{
    color: var(--color-primary) !important;
}}

.bg-primary {{
    background-color: var(--color-primary) !important;
}}

/* Sidebar theming */
.sidebar {{
    background-color: var(--sidebar-bg);
}}

/* Header theming */
.header {{
    background-color: var(--header-bg);
}}

/* Typography */
body {{
    font-family: var(--font-primary);
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-secondary);
}}
"""
    
    # Append custom CSS if provided
    if theme.custom_css:
        css += f"\n\n/* Custom CSS */\n{theme.custom_css}"
    
    return css


# Default Theme
DEFAULT_THEME = {
    "primary_color": "#8b5cf6",
    "secondary_color": "#3b82f6",
    "accent_color": "#10b981",
    "success_color": "#10b981",
    "warning_color": "#f59e0b",
    "error_color": "#ef4444",
    "font_family_primary": "Inter, system-ui, sans-serif",
    "sidebar_background": "#1f2937",
    "header_background": "#ffffff",
    "features_config": {
        "enable_dark_mode": True,
        "enable_notifications": True,
        "enable_exports": True,
        "enable_ai_insights": True,
        "enable_custom_reports": True
    }
}
