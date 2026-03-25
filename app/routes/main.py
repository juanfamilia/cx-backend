from fastapi import APIRouter
from app.routes import (
    auth_router,
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
    evaluation_analysis_router,
    evaluation_event_router,
    evaluation_router,
    notification_router,
    survey_router,
    user_router,
    payment_router,
    user_zone_router,
    zone_router,
    transcript_segment_router,
    executive_router,
)


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(company_router)
api_router.include_router(payment_router)
api_router.include_router(zone_router)
api_router.include_router(user_zone_router)
api_router.include_router(survey_router)
api_router.include_router(campaign_router)
api_router.include_router(campaign_assignment_router)
api_router.include_router(campaign_assigment_users_router)
api_router.include_router(campaign_assigment_zones_router)
api_router.include_router(evaluation_router)
api_router.include_router(notification_router)
api_router.include_router(dashboard_router)
api_router.include_router(cloudflare_router)
api_router.include_router(cloudflare_webhook_router)
api_router.include_router(evaluation_analysis_router)
api_router.include_router(evaluation_event_router)
api_router.include_router(campaign_goals_evaluator_router)
api_router.include_router(campaign_goals_progress_router)
api_router.include_router(transcript_segment_router)
api_router.include_router(executive_router)
