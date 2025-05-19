from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middlewares.error_middleware import db_exception_handler
from app.routes.main import api_router
from app.core.config import settings

app = FastAPI()
app.title = settings.PROJECT_NAME

origins = ["http://localhost:4200"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(db_exception_handler)

# Routing
app.include_router(api_router, prefix=settings.API_URL)
