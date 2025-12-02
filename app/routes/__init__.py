# app/routes/__init__.py

from .widget_router import router as widget_router
from .auth_router import auth_router
from .campaign_router import campaign_router
from .campaign_assignment_router import campaign_assignment_router
from .campaign_assigment_users_router import campaign_assigment_users_router
from .campaign_assigment_zones_router import campaign_assigment_zones_router
from .campaign_goals_evaluator_router import campaign_goals_evaluator_router
from .campaign_goals_progress_router import campaign_goals_progress_router
from .cloudflare_router import cloudflare_router
from .cloudflare_webhook_router import cloudflare_webhook_router
from .company_router import company_router
from .dashboard_router import dashboard_router
from .dashboard_config_router import dashboard_config_router
from .evaluation_router import evaluation_router
from .evaluation_analysis_router import evaluation_analysis_router  # solo si existe el .py
from .intelligence_router import intelligence_router
from .notification_router import notification_router
from .payment_router import payment_router
from .prompt_manager_router import prompt_manager_router
from .survey_router import survey_router
from .theme_router import theme_router
from .user_router import user_router
from .user_zone_router import user_zone_router
from .zone_router import zone_router
