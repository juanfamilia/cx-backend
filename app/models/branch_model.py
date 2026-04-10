from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from app.types.pagination import Pagination

if TYPE_CHECKING:
    from app.models.evaluation_model import Evaluation
    from app.models.zone_model import Zone


class BranchBase(SQLModel):
    company_id: int = Field(foreign_key="companies.id", index=True)
    zone_id: Optional[int] = Field(default=None, foreign_key="zones.id", index=True)
    name: str = Field(index=True)
    code: str = Field(index=True, description="Identificador externo, ej: SUC-001")
    address: Optional[str] = Field(default=None)
    country: str = Field(default="DO")
    is_active: bool = Field(default=True)


class Branch(BranchBase, table=True):
    __tablename__ = "branches"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=func.now()))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now())
    )
    deleted_at: Optional[datetime] = Field(default=None)

    evaluations: List["Evaluation"] = Relationship(
        back_populates="branch", sa_relationship_kwargs={"lazy": "noload"}
    )


class BranchCreate(SQLModel):
    company_id: int
    zone_id: Optional[int] = None
    name: str
    code: str
    address: Optional[str] = None
    country: str = "DO"
    is_active: bool = True


class BranchUpdate(SQLModel):
    zone_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class BranchPublic(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class BranchesPublic(BaseModel):
    data: List[BranchPublic]
    pagination: Pagination


class BranchImportRow(BaseModel):
    """Fila para importación masiva vía CSV/Excel"""
    code: str
    name: str
    zone_id: Optional[int] = None
    address: Optional[str] = None
    country: str = "DO"


class BranchImportResult(BaseModel):
    created: int
    updated: int
    errors: List[str]
