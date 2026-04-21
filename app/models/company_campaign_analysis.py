import json
from typing import Any

from pydantic import field_validator
from sqlalchemy import ARRAY, Column, JSON
from sqlmodel import Field, SQLModel


class CompanyCampaignAnalysis(SQLModel, table=True):
    __tablename__ = "company_campaign_analysis"

    company_id: int = Field(primary_key=True)
    campaign_id: int = Field(primary_key=True)
    campaign_name: str

    # ARRAY(JSON): el driver a veces entrega cada elemento como str JSON → coerción antes de serializar.
    operative_views: list[dict[str, Any]] = Field(sa_column=Column(ARRAY(JSON)))

    @field_validator("operative_views", mode="before")
    @classmethod
    def _coerce_operative_views(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, (list, tuple)):
            return v
        out: list[Any] = []
        for item in v:
            if isinstance(item, str):
                try:
                    parsed = json.loads(item)
                    out.append(parsed if isinstance(parsed, dict) else {"value": parsed})
                except json.JSONDecodeError:
                    out.append({"raw": item})
            elif isinstance(item, dict):
                out.append(item)
            else:
                out.append({"value": item})
        return out
