from fastapi import APIRouter
from app.routes import (
    auth_router,
    widget_router,
    campaign_assigment_users_router,
    campaign_assigment_zones_router,
    campaign_assignment_router,
    campaign_goals_evaluator_router,
    campaign_goals_progress_router,
    campaign_router,
    cloudflare_router,
    cloudflare_webhook_router,
    company_router,
    dashboard_router,
    dashboard_config_router,
    evaluation_analysis_router,
    evaluation_router,
    intelligence_router,
    notification_router,
    payment_router,
    prompt_manager_router,
    survey_router,
    theme_router,
    user_router,
    user_zone_router,
    zone_router,
)


api_router = APIRouter()

api_router.include_router(widget_router.router)
api_router.include_router(auth_router.router)
api_router.include_router(user_router.router)
api_router.include_router(company_router.router)
api_router.include_router(payment_router.router)
api_router.include_router(zone_router.router)
api_router.include_router(user_zone_router.router)
api_router.include_router(survey_router.router)
api_router.include_router(campaign_router.router)
api_router.include_router(campaign_assignment_router.router)
api_router.include_router(campaign_assigment_users_router.router)
api_router.include_router(campaign_assigment_zones_router.router)
api_router.include_router(evaluation_router.router)
api_router.include_router(notification_router.router)
api_router.include_router(dashboard_router.router)
api_router.include_router(dashboard_config_router.router)
api_router.include_router(cloudflare_router.router)
api_router.include_router(cloudflare_webhook_router.router)
api_router.include_router(evaluation_analysis_router.router)
api_router.include_router(campaign_goals_evaluator_router.router)
api_router.include_router(campaign_goals_progress_router.router)
api_router.include_router(prompt_manager_router.router)
api_router.include_router(intelligence_router.router)
api_router.include_router(theme_router.router)
