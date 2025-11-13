from typing import List, Dict
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, ARRAY


class CompanyCampaignAnalysis(SQLModel, table=True):
    __tablename__ = "company_campaign_analysis"

    company_id: int = Field(primary_key=True)
    campaign_id: int = Field(primary_key=True)
    campaign_name: str

    # Columna tipo ARRAY de JSON (equivalente a jsonb[] en Postgres)
    operative_views: List[Dict] = Field(
        sa_column=Column(ARRAY(JSON))
    )
