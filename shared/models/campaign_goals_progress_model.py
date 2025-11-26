from datetime import datetime

from sqlmodel import Field, SQLModel


class CampaignGoalsProgress(SQLModel, table=True):
    __tablename__ = "campaign_goals_progress"
    campaign_id: int = Field(primary_key=True)
    campaign_name: str
    evaluator_id: int = Field(primary_key=True)
    goal_evaluator: int
    goal_complete: int
    date_start: datetime
    date_end: datetime
