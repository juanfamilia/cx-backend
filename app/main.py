from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main import api_router
from app.core.config import settings

# config
app = FastAPI(
    docs_url="/docs",           # Swagger UI en /docs
    redoc_url="/redoc",         # ReDoc en /redoc (opcional)
    openapi_url="/openapi.json" # Esquema OpenAPI
)

app.title = settings.PROJECT_NAME

# CORS Configuration - Allow specific origins for production
origins = [
   # "https://cx-frontendnew.vercel.app",
   # "http://localhost:3000",
   # "http://localhost:4200",
    "*"  # Fallback for development
]

# app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# app.middleware("http")(db_exception_handler)

# Routing
app.include_router(api_router, prefix=settings.API_URL)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

