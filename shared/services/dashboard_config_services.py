from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.dashboard_config_model import (
    DashboardConfig,
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigPublic,
    DashboardConfigsPublic,
    WidgetDefinition,
    WidgetDefinitionBase,
    WidgetDefinitionPublic,
    WidgetDefinitionsPublic,
)
from app.utils.exeptions import NotFoundException


# Dashboard Configuration Services

async def get_user_dashboard_configs(
    session: AsyncSession, user_id: int
) -> DashboardConfigsPublic:
    """Get all dashboard configurations for a user"""
    
    # Count query
    count_query = select(func.count(DashboardConfig.id)).where(
        DashboardConfig.user_id == user_id,
        DashboardConfig.deleted_at == None
    )
    count_result = await session.execute(count_query)
    total = count_result.scalar()
    
    # Data query
    query = select(DashboardConfig).where(
        DashboardConfig.user_id == user_id,
        DashboardConfig.deleted_at == None
    ).order_by(DashboardConfig.is_default.desc(), DashboardConfig.created_at.desc())
    
    result = await session.execute(query)
    configs = result.scalars().all()
    
    return DashboardConfigsPublic(data=configs, total=total)


async def get_default_dashboard_config(
    session: AsyncSession, user_id: int
) -> DashboardConfigPublic | None:
    """Get the default dashboard configuration for a user"""
    query = select(DashboardConfig).where(
        DashboardConfig.user_id == user_id,
        DashboardConfig.is_default == True,
        DashboardConfig.deleted_at == None
    )
    result = await session.execute(query)
    config = result.scalars().first()
    
    return config


async def get_dashboard_config_by_id(
    session: AsyncSession, config_id: int
) -> DashboardConfigPublic:
    """Get a specific dashboard configuration"""
    query = select(DashboardConfig).where(
        DashboardConfig.id == config_id,
        DashboardConfig.deleted_at == None
    )
    result = await session.execute(query)
    config = result.scalars().first()
    
    if not config:
        raise NotFoundException("Dashboard configuration not found")
    
    return config


async def create_dashboard_config(
    session: AsyncSession, config_data: DashboardConfigCreate
) -> DashboardConfigPublic:
    """Create a new dashboard configuration"""
    
    # If setting as default, unset other defaults
    if config_data.is_default:
        await unset_default_configs(session, config_data.user_id)
    
    db_config = DashboardConfig(**config_data.model_dump())
    session.add(db_config)
    await session.commit()
    await session.refresh(db_config)
    
    return db_config


async def update_dashboard_config(
    session: AsyncSession, config_id: int, config_data: DashboardConfigUpdate
) -> DashboardConfigPublic:
    """Update an existing dashboard configuration"""
    db_config = await get_dashboard_config_by_id(session, config_id)
    
    # If setting as default, unset other defaults
    if config_data.is_default and not db_config.is_default:
        await unset_default_configs(session, db_config.user_id, exclude_id=config_id)
    
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    session.add(db_config)
    await session.commit()
    await session.refresh(db_config)
    
    return db_config


async def unset_default_configs(
    session: AsyncSession, user_id: int, exclude_id: int | None = None
):
    """Unset default flag on all configs for a user"""
    query = select(DashboardConfig).where(
        DashboardConfig.user_id == user_id,
        DashboardConfig.is_default == True,
        DashboardConfig.deleted_at == None
    )
    
    if exclude_id:
        query = query.where(DashboardConfig.id != exclude_id)
    
    result = await session.execute(query)
    configs = result.scalars().all()
    
    for config in configs:
        config.is_default = False
        session.add(config)
    
    await session.commit()


async def soft_delete_dashboard_config(
    session: AsyncSession, config_id: int
) -> DashboardConfigPublic:
    """Soft delete a dashboard configuration"""
    db_config = await get_dashboard_config_by_id(session, config_id)
    db_config.deleted_at = datetime.now()
    
    session.add(db_config)
    await session.commit()
    await session.refresh(db_config)
    
    return db_config


# Widget Definition Services

async def get_available_widgets(
    session: AsyncSession, role: int | None = None
) -> WidgetDefinitionsPublic:
    """Get all available widget definitions, optionally filtered by role"""
    
    query = select(WidgetDefinition).where(WidgetDefinition.is_active == True)
    
    result = await session.execute(query)
    widgets = result.scalars().all()
    
    # Filter by role if specified
    if role is not None:
        widgets = [w for w in widgets if role in w.available_for_roles]
    
    return WidgetDefinitionsPublic(data=widgets, total=len(widgets))


async def get_widget_definition_by_type(
    session: AsyncSession, widget_type: str
) -> WidgetDefinitionPublic:
    """Get a widget definition by type"""
    query = select(WidgetDefinition).where(
        WidgetDefinition.widget_type == widget_type,
        WidgetDefinition.is_active == True
    )
    result = await session.execute(query)
    widget = result.scalars().first()
    
    if not widget:
        raise NotFoundException(f"Widget type '{widget_type}' not found")
    
    return widget


async def create_widget_definition(
    session: AsyncSession, widget_data: WidgetDefinitionBase
) -> WidgetDefinitionPublic:
    """Create a new widget definition (admin only)"""
    db_widget = WidgetDefinition(**widget_data.model_dump())
    session.add(db_widget)
    await session.commit()
    await session.refresh(db_widget)
    
    return db_widget


# Default Dashboard Layouts by Role

def get_default_layout_for_role(role: int) -> dict:
    """Get default dashboard layout based on user role"""
    
    # Default layouts for each role
    layouts = {
        0: {  # Superadmin
            "layout_version": "1.0",
            "grid_columns": 12,
            "widgets": [
                {
                    "widget_id": "total_companies",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 0, "width": 3, "height": 1},
                    "config": {
                        "title": "Total Companies",
                        "metric": "total_companies",
                        "icon": "building",
                        "color": "blue"
                    }
                },
                {
                    "widget_id": "total_users",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 3, "width": 3, "height": 1},
                    "config": {
                        "title": "Total Users",
                        "metric": "total_users",
                        "icon": "users",
                        "color": "green"
                    }
                },
                {
                    "widget_id": "total_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 6, "width": 3, "height": 1},
                    "config": {
                        "title": "Total Evaluations",
                        "metric": "total_evaluations",
                        "icon": "clipboard-check",
                        "color": "purple"
                    }
                },
                {
                    "widget_id": "active_campaigns",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 9, "width": 3, "height": 1},
                    "config": {
                        "title": "Active Campaigns",
                        "metric": "active_campaigns",
                        "icon": "target",
                        "color": "orange"
                    }
                },
                {
                    "widget_id": "companies_table",
                    "widget_type": "data_table",
                    "position": {"row": 1, "col": 0, "width": 12, "height": 3},
                    "config": {
                        "title": "Companies Overview",
                        "data_source": "/dashboard/widgets/companies-summary"
                    }
                }
            ]
        },
        1: {  # Admin
            "layout_version": "1.0",
            "grid_columns": 12,
            "widgets": [
                {
                    "widget_id": "total_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 0, "width": 3, "height": 1},
                    "config": {
                        "title": "Total Evaluations",
                        "metric": "total_evaluations",
                        "icon": "clipboard-check",
                        "color": "blue"
                    }
                },
                {
                    "widget_id": "completed_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 3, "width": 3, "height": 1},
                    "config": {
                        "title": "Completed",
                        "metric": "completed_evaluations",
                        "icon": "check-circle",
                        "color": "green"
                    }
                },
                {
                    "widget_id": "pending_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 6, "width": 3, "height": 1},
                    "config": {
                        "title": "Pending",
                        "metric": "pending_evaluations",
                        "icon": "clock",
                        "color": "orange"
                    }
                },
                {
                    "widget_id": "avg_nps",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 9, "width": 3, "height": 1},
                    "config": {
                        "title": "Avg NPS",
                        "metric": "avg_nps",
                        "icon": "star",
                        "color": "purple",
                        "format": "decimal"
                    }
                },
                {
                    "widget_id": "nps_trend",
                    "widget_type": "line_chart",
                    "position": {"row": 1, "col": 0, "width": 6, "height": 2},
                    "config": {
                        "title": "NPS Trend (30 days)",
                        "data_source": "/dashboard/widgets/nps-trend"
                    }
                },
                {
                    "widget_id": "evaluation_status",
                    "widget_type": "pie_chart",
                    "position": {"row": 1, "col": 6, "width": 3, "height": 2},
                    "config": {
                        "title": "Evaluation Status",
                        "data_source": "/dashboard/widgets/status-breakdown"
                    }
                },
                {
                    "widget_id": "top_evaluators",
                    "widget_type": "data_table",
                    "position": {"row": 1, "col": 9, "width": 3, "height": 2},
                    "config": {
                        "title": "Top Evaluators",
                        "data_source": "/dashboard/widgets/top-evaluators",
                        "limit": 5
                    }
                }
            ]
        },
        2: {  # Manager
            "layout_version": "1.0",
            "grid_columns": 12,
            "widgets": [
                {
                    "widget_id": "assigned_campaigns",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 0, "width": 4, "height": 1},
                    "config": {
                        "title": "My Campaigns",
                        "metric": "assigned_campaigns",
                        "icon": "target",
                        "color": "blue"
                    }
                },
                {
                    "widget_id": "total_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 4, "width": 4, "height": 1},
                    "config": {
                        "title": "Evaluations",
                        "metric": "total_evaluations",
                        "icon": "clipboard-check",
                        "color": "green"
                    }
                },
                {
                    "widget_id": "avg_nps",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 8, "width": 4, "height": 1},
                    "config": {
                        "title": "Avg NPS",
                        "metric": "avg_nps",
                        "icon": "star",
                        "color": "purple",
                        "format": "decimal"
                    }
                },
                {
                    "widget_id": "campaigns_list",
                    "widget_type": "data_table",
                    "position": {"row": 1, "col": 0, "width": 12, "height": 2},
                    "config": {
                        "title": "My Campaigns",
                        "data_source": "/dashboard/widgets/manager-campaigns"
                    }
                }
            ]
        },
        3: {  # Shopper
            "layout_version": "1.0",
            "grid_columns": 12,
            "widgets": [
                {
                    "widget_id": "total_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 0, "width": 4, "height": 1},
                    "config": {
                        "title": "My Evaluations",
                        "metric": "total_evaluations_submitted",
                        "icon": "clipboard-check",
                        "color": "blue"
                    }
                },
                {
                    "widget_id": "completed_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 4, "width": 4, "height": 1},
                    "config": {
                        "title": "Completed",
                        "metric": "completed_evaluations",
                        "icon": "check-circle",
                        "color": "green"
                    }
                },
                {
                    "widget_id": "pending_evaluations",
                    "widget_type": "kpi_card",
                    "position": {"row": 0, "col": 8, "width": 4, "height": 1},
                    "config": {
                        "title": "Pending",
                        "metric": "pending_evaluations",
                        "icon": "clock",
                        "color": "orange"
                    }
                },
                {
                    "widget_id": "active_campaigns",
                    "widget_type": "data_table",
                    "position": {"row": 1, "col": 0, "width": 12, "height": 2},
                    "config": {
                        "title": "Active Campaigns",
                        "data_source": "/dashboard/widgets/shopper-campaigns"
                    }
                }
            ]
        }
    }
    
    return layouts.get(role, layouts[3])  # Default to shopper layout if unknown role
