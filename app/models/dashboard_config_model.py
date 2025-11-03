from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func
from sqlalchemy import JSON
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.user_model import User


class DashboardConfigBase(SQLModel):
    """Base model for user dashboard configuration"""
    user_id: int = Field(foreign_key="users.id")
    layout_config: dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="JSON configuration for dashboard layout"
    )
    is_default: bool = Field(default=False, description="Whether this is the default layout")
    config_name: str = Field(max_length=100, description="Name for this configuration")


class DashboardConfigCreate(DashboardConfigBase):
    """Schema for creating a dashboard configuration"""
    pass


class DashboardConfigUpdate(SQLModel):
    """Schema for updating dashboard configuration"""
    layout_config: dict[str, Any] | None = None
    is_default: bool | None = None
    config_name: str | None = None


class DashboardConfig(DashboardConfigBase, table=True):
    """Database table for dashboard configurations"""
    __tablename__ = "dashboard_configs"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(default=None)
    
    user: "User" = Relationship(
        back_populates="dashboard_configs", sa_relationship_kwargs={"lazy": "noload"}
    )


class DashboardConfigPublic(DashboardConfigBase):
    """Public schema for dashboard configuration"""
    id: int
    created_at: datetime
    updated_at: datetime


class DashboardConfigsPublic(SQLModel):
    """List response for dashboard configurations"""
    data: list[DashboardConfigPublic]
    total: int


# Widget Definitions Catalog
class WidgetDefinitionBase(SQLModel):
    """Base model for available widget types"""
    widget_type: str = Field(description="Type identifier (e.g., 'kpi_card', 'line_chart', 'bar_chart')")
    widget_name: str = Field(description="Display name for the widget")
    description: str = Field(description="What this widget displays")
    data_source: str = Field(description="API endpoint or data source identifier")
    default_config: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Default configuration for this widget type"
    )
    available_for_roles: list[int] = Field(
        sa_column=Column(JSON),
        description="List of role IDs that can use this widget"
    )
    category: str = Field(default="general", description="Widget category (metrics, charts, lists, etc.)")


class WidgetDefinition(WidgetDefinitionBase, table=True):
    """Database table for widget catalog"""
    __tablename__ = "widget_definitions"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    is_active: bool = Field(default=True, description="Whether this widget is available")


class WidgetDefinitionPublic(WidgetDefinitionBase):
    """Public schema for widget definition"""
    id: int
    is_active: bool
    created_at: datetime


class WidgetDefinitionsPublic(SQLModel):
    """List response for widget definitions"""
    data: list[WidgetDefinitionPublic]
    total: int


# Layout Config JSON Schema Example:
"""
{
  "layout_version": "1.0",
  "grid_columns": 12,
  "widgets": [
    {
      "widget_id": "total_evaluations_kpi",
      "widget_type": "kpi_card",
      "position": {"row": 0, "col": 0, "width": 3, "height": 1},
      "config": {
        "title": "Total Evaluations",
        "metric": "total_evaluations",
        "format": "number",
        "icon": "chart-bar",
        "color": "blue"
      }
    },
    {
      "widget_id": "nps_trend_chart",
      "widget_type": "line_chart",
      "position": {"row": 1, "col": 0, "width": 6, "height": 2},
      "config": {
        "title": "NPS Trend",
        "data_source": "/dashboard/widgets/nps-trend",
        "x_axis": "date",
        "y_axis": "nps_score",
        "date_range": "30d"
      }
    },
    {
      "widget_id": "evaluation_status_pie",
      "widget_type": "pie_chart",
      "position": {"row": 1, "col": 6, "width": 3, "height": 2},
      "config": {
        "title": "Evaluation Status",
        "data_source": "/dashboard/widgets/status-breakdown",
        "labels": ["Completed", "Pending", "Analyzing"],
        "colors": ["#10b981", "#f59e0b", "#3b82f6"]
      }
    }
  ]
}
"""
