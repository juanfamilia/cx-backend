# app/routes/__init__.py

from .widget_router import router as widget_router
from .auth_router import router as auth_router
from .campaign_router import router as campaign_router
from .campaign_assignment_router import router as campaign_assignment_router
from .campaign_assigment_users_router import router as campaign_assigment_users_router
from .campaign_assigment_zones_router import router as campaign_assigment_zones_router
from .campaign_goals_evaluator_router import router as campaign_goals_evaluator_router
from .campaign_goals_progress_router import router as campaign_goals_progress_router
from .cloudflare_router import router as cloudflare_router
from .cloudflare_webhook_router import router as cloudflare_webhook_router
from .company_router import router as company_router
from .dashboard_router import router as dashboard_router
from .dashboard_config_router import router as dashboard_config_router
from .evaluation_router import router as evaluation_router
from .intelligence_router import router as intelligence_router
from .notification_router import router as notification_router
from .payment_router import router as payment_router
from .prompt_manager_router import router as prompt_manager_router
from .survey_router import router as survey_router
from .theme_router import router as theme_router
from .user_router import router as user_router
from .user_zone_router import router as user_zone_router
from .zone_router import router as zone_router


