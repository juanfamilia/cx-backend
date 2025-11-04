from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime

class WidgetBase(SQLModel):
    """Clase base para widgets en el dashboard"""
    name: str
    description: str | None = None
    type: str
    settings: dict | None = Field(default=None, sa_column=Column(JSON))
    order: int | None = None

class Widget(WidgetBase, table=True):
    """Tabla en la base para widgets del dashboard"""
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
