from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime, func, JSON
from pydantic import BaseModel

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.company_model import Company

class WidgetType(str, Enum):
    """Tipos de widgets disponibles"""
    METRIC_CARD = "metric_card"          # KPI simple (número + título)
    LINE_CHART = "line_chart"            # Gráfico de línea temporal
    BAR_CHART = "bar_chart"              # Gráfico de barras
    PIE_CHART = "pie_chart"              # Gráfico circular
    TABLE = "table"                       # Tabla de datos
    MAP = "map"                           # Mapa geográfico
    HEATMAP = "heatmap"                   # Mapa de calor
    LEADERBOARD = "leaderboard"           # Ranking/clasificación
    RECENT_ACTIVITY = "recent_activity"   # Timeline de actividad
    ALERTS = "alerts"                     # Panel de alertas

class DataSource(str, Enum):
    """Fuentes de datos para widgets"""
    EVALUATIONS = "evaluations"
    CAMPAIGNS = "campaigns"
    USERS = "users"
    ZONES = "zones"
    CUSTOM = "custom"

# --- MODELOS BASE ---

class WidgetBase(SQLModel):
    """Propiedades compartidas de Widget"""
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    type: WidgetType
    
    # Restricción por rol (None = todos)
    role_restriction: int | None = Field(default=None)
    # 1 = admin, 2 = manager, 3 = evaluator, None = all roles
    
    # Configuración del widget
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Ejemplo: {"metric": "nps", "period": "30d", "comparison": true}
    
    # Posición por defecto en grid (cols, rows basado en gridster)
    default_position: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "cols": 4, "rows": 2}, sa_column=Column(JSON))
    
    # Datos
    data_source: DataSource
    query_params: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Ejemplo: {"status": "completed", "date_from": "2025-01-01"}
    
    # Visibilidad
    is_public: bool = True  # Si false, solo visible para quien lo creó
    is_active: bool = True

class WidgetCreate(WidgetBase):
    """Schema para crear widget"""
    company_id: int | None = None

class WidgetUpdate(SQLModel):
    """Schema para actualizar widget"""
    name: str | None = None
    description: str | None = None
    type: WidgetType | None = None
    config: dict | None = None
    default_position: dict | None = None
    data_source: DataSource | None = None
    query_params: dict | None = None
    is_public: bool | None = None
    is_active: bool | None = None

# --- MODELO DE TABLA ---

class Widget(WidgetBase, table=True):
    """Tabla de widgets del sistema"""
    __tablename__ = "widgets"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # Multi-tenancy: widgets específicos de company o globales
    company_id: int | None = Field(default=None, foreign_key="companies.id", nullable=True)
    
    # Timestamps
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now()))
    deleted_at: datetime | None = Field(default=None)
    
    # Relaciones
    company: Optional["Company"] = Relationship(back_populates="widgets")
    user_widgets: list["UserDashboardWidget"] = Relationship(back_populates="widget")

class WidgetPublic(WidgetBase):
    """Schema público de widget"""
    id: int
    company_id: int | None
    created_at: datetime
    updated_at: datetime

# --- USER DASHBOARD WIDGETS (Personalización por usuario) ---

class UserDashboardWidgetBase(SQLModel):
    """Widgets asignados a dashboard de usuario"""
    user_id: int = Field(foreign_key="users.id")
    widget_id: int = Field(foreign_key="widgets.id")
    
    # Posición personalizada (override de default_position)
    position: dict = Field(sa_column=Column(JSON))
    # Ejemplo: {"x": 0, "y": 0, "cols": 6, "rows": 3}
    
    # Config personalizada (override de widget.config)
    custom_config: dict | None = Field(default=None, sa_column=Column(JSON))
    
    is_visible: bool = True
    order: int = 0  # Para ordenamiento manual

class UserDashboardWidgetCreate(UserDashboardWidgetBase):
    """Schema para crear widget de usuario"""
    pass

class UserDashboardWidget(UserDashboardWidgetBase, table=True):
    """Tabla de widgets personalizados por usuario"""
    __tablename__ = "user_dashboard_widgets"
    
    id: int | None = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=func.now(), onupdate=func.now()))
    
    # Relaciones
    user: "User" = Relationship(back_populates="dashboard_widgets")
    widget: Widget = Relationship(back_populates="user_widgets")

class UserDashboardWidgetPublic(UserDashboardWidgetBase):
    """Schema público"""
    id: int
    widget: WidgetPublic
    created_at: datetime

# --- SCHEMAS DE RESPUESTA ---

class UserDashboardResponse(BaseModel):
    """Respuesta del dashboard completo de un usuario"""
    widgets: list[UserDashboardWidgetPublic]
    layout: list[dict]  # Lista de posiciones para gridster

class WidgetDataResponse(BaseModel):
    """Respuesta con datos del widget"""
    widget_id: int
    data: dict  # Datos específicos según tipo de widget
    last_updated: datetime
