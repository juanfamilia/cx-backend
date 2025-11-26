"""
App Models - Re-exports from shared
This allows Alembic to detect models and maintains backward compatibility
"""

# Import all models from shared
from shared.models.user_model import User, UserCreate, UserUpdate, UserPublic
from shared.models.company_model import Company, CompanyCreate, CompanyUpdate, CompanyPublic
from shared.models.campaign_model import Campaign, CampaignCreate, CampaignUpdate, CampaignPublic
from shared.models.evaluation_model import Evaluation, EvaluationCreate, EvaluationUpdate, EvaluationPublic
from shared.models.evaluation_analysis_model import EvaluationAnalysis, EvaluationAnalysisCreate, EvaluationAnalysisPublic
from shared.models.zone_model import Zone, ZoneCreate, ZoneUpdate, ZonePublic
from shared.models.survey_model import Survey, SurveyCreate, SurveyUpdate, SurveyPublic
from shared.models.survey_forms_model import SurveyForm, SurveyFormCreate, SurveyFormUpdate, SurveyFormPublic
from shared.models.notification_model import Notification, NotificationCreate, NotificationUpdate, NotificationPublic
from shared.models.payment_model import Payment, PaymentCreate, PaymentUpdate, PaymentPublic
from shared.models.dashboard_config_model import DashboardConfig, DashboardConfigCreate, DashboardConfigUpdate, DashboardConfigPublic
from shared.models.intelligence_model import Intelligence, IntelligenceCreate, IntelligencePublic
from shared.models.prompt_manager_model import PromptManager, PromptManagerCreate, PromptManagerUpdate, PromptManagerPublic
from shared.models.theme_model import Theme, ThemeCreate, ThemeUpdate, ThemePublic
from shared.models.widget_model import Widget, WidgetCreate, WidgetUpdate, WidgetPublic
from shared.models.video_model import Video, VideoCreate, VideoUpdate, VideoPublic
from shared.models.campaign_user_model import CampaignUser, CampaignUserCreate
from shared.models.campaign_zone_model import CampaignZone, CampaignZoneCreate
from shared.models.user_zone_model import UserZone, UserZoneCreate
from shared.models.onboarding_model import Onboarding, OnboardingCreate, OnboardingUpdate
from shared.models.campaign_goals_evaluator_model import CampaignGoalsEvaluator, CampaignGoalsEvaluatorCreate
from shared.models.campaign_goals_progress_model import CampaignGoalsProgress, CampaignGoalsProgressCreate
from shared.models.user_evaluation_summary_model import UserEvaluationSummary, UserEvaluationSummaryPublic

# Re-export all for Alembic and backward compatibility
__all__ = [
    "User", "UserCreate", "UserUpdate", "UserPublic",
    "Company", "CompanyCreate", "CompanyUpdate", "CompanyPublic",
    "Campaign", "CampaignCreate", "CampaignUpdate", "CampaignPublic",
    "Evaluation", "EvaluationCreate", "EvaluationUpdate", "EvaluationPublic",
    "EvaluationAnalysis", "EvaluationAnalysisCreate", "EvaluationAnalysisPublic",
    "Zone", "ZoneCreate", "ZoneUpdate", "ZonePublic",
    "Survey", "SurveyCreate", "SurveyUpdate", "SurveyPublic",
    "SurveyForm", "SurveyFormCreate", "SurveyFormUpdate", "SurveyFormPublic",
    "Notification", "NotificationCreate", "NotificationUpdate", "NotificationPublic",
    "Payment", "PaymentCreate", "PaymentUpdate", "PaymentPublic",
    "DashboardConfig", "DashboardConfigCreate", "DashboardConfigUpdate", "DashboardConfigPublic",
    "Intelligence", "IntelligenceCreate", "IntelligencePublic",
    "PromptManager", "PromptManagerCreate", "PromptManagerUpdate", "PromptManagerPublic",
    "Theme", "ThemeCreate", "ThemeUpdate", "ThemePublic",
    "Widget", "WidgetCreate", "WidgetUpdate", "WidgetPublic",
    "Video", "VideoCreate", "VideoUpdate", "VideoPublic",
    "CampaignUser", "CampaignUserCreate",
    "CampaignZone", "CampaignZoneCreate",
    "UserZone", "UserZoneCreate",
    "Onboarding", "OnboardingCreate", "OnboardingUpdate",
    "CampaignGoalsEvaluator", "CampaignGoalsEvaluatorCreate",
    "CampaignGoalsProgress", "CampaignGoalsProgressCreate",
    "UserEvaluationSummary", "UserEvaluationSummaryPublic",
]
