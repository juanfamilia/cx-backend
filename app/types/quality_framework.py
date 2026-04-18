"""Tipos públicos para la API del Service Quality Framework."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.framework_model import FrameworkPublic
from app.types.pagination import Pagination


class FrameworkListResponse(BaseModel):
    data: List[FrameworkPublic]
    pagination: Pagination


class SuggestedSurveyAspectItem(BaseModel):
    """Sugerencia para crear aspectos de formulario desde el template de industria."""

    competency_id: int
    competency_code: str
    name: str
    suggested_description: str
    suggested_type: str = Field(
        description="AspectTypeEnum del backend: number|boolean|likert|compliance|media"
    )
    suggested_order: int = 0
    weight_hint: float = 1.0
    is_mandatory: bool = False


class SuggestedSurveyAspectsResponse(BaseModel):
    company_id: int
    industry_id: Optional[int] = None
    items: List[SuggestedSurveyAspectItem]
