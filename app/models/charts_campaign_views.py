from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel


class CampaignGoalsWeeklyProgress(SQLModel, table=True):
    __tablename__ = "campaign_goals_weekly_progress"
    campaign_id: int
    campaign_name: str
    evaluator_id: int = Field(primary_key=True)
    day_name: str
    day_date: date
    goal_weekly: float
    daily_goal: float
    reported_today: int


class CampaignGoalsCoverage(SQLModel, table=True):
    __tablename__ = "campaign_goals_coverage"
    campaign_id: int
    campaign_name: str
    evaluator_id: int = Field(primary_key=True)
    goal_weekly: float
    reported_total: int
    coverage_percent: float
