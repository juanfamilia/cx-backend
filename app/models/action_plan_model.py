from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Text
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination


class ActionPlanStatus(str, Enum):
    PENDING    = "pending"     # Generado, sin acción del responsable
    IN_PROGRESS = "in_progress"  # Responsable tomó el caso
    RESOLVED   = "resolved"   # Corrección aplicada
    OVERDUE    = "overdue"     # Venció sin resolverse
    CANCELLED  = "cancelled"


class ActionPlanPriority(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class ActionPlanBase(SQLModel):
    evaluation_id: int = Field(foreign_key="evaluations.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True)

    # Asignación
    assigned_to_user_id: Optional[int] = Field(
        default=None, foreign_key="users.id", index=True,
        description="Gerente o supervisor responsable de la corrección"
    )
    created_by_user_id: Optional[int] = Field(
        default=None, foreign_key="users.id",
        description="Quién generó el plan (puede ser automático vía IA)"
    )

    # Contenido
    title: str
    description: str = Field(sa_column=Column(Text))
    priority: ActionPlanPriority = Field(default=ActionPlanPriority.MEDIUM)
    status: ActionPlanStatus = Field(default=ActionPlanStatus.PENDING)

    # Seguimiento
    due_date: Optional[date] = Field(default=None, description="Fecha límite de resolución")
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True),
        description="Qué acciones tomó el responsable"
    )

    # Re-evaluación
    requires_reevaluation: bool = Field(
        default=False,
        description="Si True, se debe generar una nueva evaluación de esta sucursal"
    )
    reevaluation_due_date: Optional[date] = Field(default=None)

    # Origen
    source: str = Field(
        default="manual",
        description="manual | ai_auto (generado automáticamente por el pipeline)"
    )


class ActionPlan(ActionPlanBase, table=True):
    __tablename__ = "action_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)


class ActionPlanCreate(BaseModel):
    evaluation_id: int
    title: str
    description: str
    priority: ActionPlanPriority = ActionPlanPriority.MEDIUM
    assigned_to_user_id: Optional[int] = None
    due_date: Optional[date] = None
    requires_reevaluation: bool = False
    reevaluation_due_date: Optional[date] = None
    source: str = "manual"


class ActionPlanUpdate(BaseModel):
    assigned_to_user_id: Optional[int] = None
    status: Optional[ActionPlanStatus] = None
    priority: Optional[ActionPlanPriority] = None
    due_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    requires_reevaluation: Optional[bool] = None
    reevaluation_due_date: Optional[date] = None


class ActionPlanPublic(ActionPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class ActionPlansPublic(BaseModel):
    data: List[ActionPlanPublic]
    pagination: Pagination
