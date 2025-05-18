from fastapi import APIRouter
from app.routes import (
    auth_router,
    company_router,
    user_router,
    payment_router,
)


api_router = APIRouter()

api_router.include_router(auth_router.router)
api_router.include_router(user_router.router)
api_router.include_router(company_router.router)
api_router.include_router(payment_router.router)
