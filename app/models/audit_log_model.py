from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, Text
from sqlmodel import Column, DateTime, Field, SQLModel, func

from app.types.pagination import Pagination


class AuditLog(SQLModel, table=True):
    """
    Registro inmutable de cambios en entidades sensibles.
    Solo INSERT permitido; nunca UPDATE ni DELETE.
    """
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))

    # Quién hizo el cambio
    user_id: int = Field(index=True)
    user_email: str = Field()

    # Qué entidad cambió
    entity_type: str = Field(index=True, description="evaluations | evaluation_answers | ...")
    entity_id: int = Field(index=True)

    # Qué cambió
    action: str = Field(description="update | status_change | delete")
    field_name: Optional[str] = Field(default=None, description="Campo específico modificado")
    old_value: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    new_value: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # Justificación obligatoria para cambios críticos
    justification: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # Contexto adicional (IP, user agent, etc.)
    extra: Optional[Any] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class AuditLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int
    user_email: str
    entity_type: str
    entity_id: int
    action: str
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    justification: Optional[str]
    extra: Optional[Any]


class AuditLogsPublic(BaseModel):
    data: list[AuditLogPublic]
    pagination: Pagination
