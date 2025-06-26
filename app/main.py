from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main import api_router
from app.core.config import settings

# config
app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

app.title = settings.PROJECT_NAME

origins = ["https://cx.dreez.dev", "http://localhost:4200"]

# app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.middleware("http")(db_exception_handler)

# Routing
app.include_router(api_router, prefix=settings.API_URL)
