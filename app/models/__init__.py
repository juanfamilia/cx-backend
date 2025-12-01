"""
App Models - Re-exports from shared
This allows Alembic to detect models and maintains backward compatibility
"""

# Import all models from shared
from shared.models.user_model import User, UserCreate, UserUpdate, UserPublic
from shared.models.company_model import Company, CompanyUpdate, CompanyPublic
from shared.models.campaign_model import Campaign, CampaignUpdate, CampaignPublic
from shared.models.evaluation_model import Evaluation, EvaluationCreate, EvaluationUpdate, EvaluationPublic
from shared.models.evaluation_analysis_model import EvaluationAnalysis, EvaluationAnalysisPublic
from shared.models.zone_model import Zone, ZonePublic
from shared.models.survey_model import Survey, SurveyUpdate, SurveyPublic
from shared.models.survey_forms_model import SurveyForm, SurveyFormUpdate, SurveyFormPublic
from shared.models.notification_model import Notification, NotificationUpdate, NotificationPublic
from shared.models.payment_model import Payment, PaymentUpdate, PaymentPublic
from shared.models.dashboard_config_model import (
    DashboardConfig,
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigPublic,
)
from shared.models.intelligence_model import Intelligence, IntelligencePublic
from shared.models.prompt_manager_model import (
    PromptManager,
    PromptManagerCreate,
    PromptManagerUpdate,
    PromptManagerPublic,
)
from shared.models.theme_model import Theme, ThemeUpdate, ThemePublic
from shared.models.widget_model import Widget, WidgetCreate, WidgetUpdate, WidgetPublic
from shared.models.video_model import Video, VideoCreate, VideoUpdate, VideoPublic
from shared.models.campaign_user_model import CampaignUser
from shared.models.campaign_zone_model import CampaignZone
from shared.models.user_zone_model import UserZone
from shared.models.onboarding_model import Onboarding, OnboardingUpdate
from shared.models.campaign_goals_evaluator_model import CampaignGoalsEvaluator
from shared.models.campaign_goals_progress_model import CampaignGoalsProgress
from shared.models.user_evaluation_summary_model import (
    UserEvaluationSummary,
    UserEvaluationSummaryPublic,
)

# Re-export all for Alembic and backward compatibility
__all__ = [
    "User", "UserCreate", "UserUpdate", "UserPublic",
    "Company", "CompanyUpdate", "CompanyPublic",
    "Campaign", "CampaignUpdate", "CampaignPublic",
    "Evaluation", "EvaluationCreate", "EvaluationUpdate", "EvaluationPublic",
    "EvaluationAnalysis", "EvaluationAnalysisPublic",
    "Zone",  "ZonePublic",
    "Survey", "SurveyUpdate", "SurveyPublic",
    "SurveyForm", "SurveyFormUpdate", "SurveyFormPublic",
    "Notification", "NotificationUpdate", "NotificationPublic",
    "Payment", "PaymentUpdate", "PaymentPublic",
    "DashboardConfig", "DashboardConfigCreate", "DashboardConfigUpdate", "DashboardConfigPublic",
    "Intelligence", "IntelligencePublic",
    "PromptManager", "PromptManagerCreate", "PromptManagerUpdate", "PromptManagerPublic",
    "Theme", "ThemeUpdate", "ThemePublic",
    "Widget", "WidgetCreate", "WidgetUpdate", "WidgetPublic",
    "Video", "VideoCreate", "VideoUpdate", "VideoPublic",
    "CampaignUser",
    "CampaignZone",
    "UserZone",
    "Onboarding", "OnboardingUpdate",
    "CampaignGoalsEvaluator",
    "CampaignGoalsProgress",
    "UserEvaluationSummary", "UserEvaluationSummaryPublic",
]
