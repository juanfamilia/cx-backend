"""
App Models - Re-exports from shared
This allows Alembic to detect models and maintains backward compatibility
"""

# Import only DB models (table=True) from shared
from shared.models.user_model import User
from shared.models.company_model import Company
from shared.models.campaign_model import Campaign
from shared.models.evaluation_model import Evaluation
from shared.models.evaluation_analysis_model import EvaluationAnalysis
from shared.models.zone_model import Zone
from shared.models.survey_model import SurveySection, SurveyAspect
from shared.models.survey_forms_model import SurveyForm
from shared.models.notification_model import Notification
from shared.models.payment_model import Payment
from shared.models.dashboard_config_model import DashboardConfig
from shared.models.intelligence_model import Intelligence
from shared.models.prompt_manager_model import PromptManager
from shared.models.theme_model import Theme
from shared.models.widget_model import Widget
from shared.models.video_model import Video
from shared.models.campaign_user_model import CampaignUser
from shared.models.campaign_zone_model import CampaignZone
from shared.models.user_zone_model import UserZone
from shared.models.onboarding_model import Onboarding
from shared.models.campaign_goals_evaluator_model import CampaignGoalsEvaluator
from shared.models.campaign_goals_progress_model import CampaignGoalsProgress
from shared.models.user_evaluation_summary_model import UserEvaluationSummary

# Re-export all for Alembic and backward compatibility
__all__ = [
    "User",
    "Company",
    "Campaign",
    "Evaluation",
    "EvaluationAnalysis",
    "Zone",
    "SurveySection",
    "SurveyAspect",
    "SurveyForm",
    "Notification",
    "Payment",
    "DashboardConfig",
    "Intelligence",
    "PromptManager",
    "Theme",
    "Widget",
    "Video",
    "CampaignUser",
    "CampaignZone",
    "UserZone",
    "Onboarding",
    "CampaignGoalsEvaluator",
    "CampaignGoalsProgress",
    "UserEvaluationSummary",
]
