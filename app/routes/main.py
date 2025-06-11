from fastapi import APIRouter
from app.routes import (
    auth_router,
    campaign_assigment_users_router,
    campaign_assigment_zones_router,
    campaign_assignment_router,
    campaign_router,
    company_router,
    evaluation_router,
    survey_router,
    user_router,
    payment_router,
    user_zone_router,
    zone_router,
)


api_router = APIRouter()

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
