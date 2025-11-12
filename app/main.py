from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main import api_router
from app.core.config import settings

# config
if settings.PROJECT_MODE == "prod":
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
else:
    app = FastAPI()

app.title = settings.PROJECT_NAME

if settings.PROJECT_MODE == "prod":
    origins = ["https://cx.sieteic.com", "https://shiny-potato-vjqwqw59wp5hx9w5-4200.app.github.dev"]
else:
    origins = ["https://cx.sieteic.com", "http://localhost:4200"]

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
