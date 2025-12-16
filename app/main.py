from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routes.main import api_router
from app.core.config import settings
import os

app = FastAPI(docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.title = settings.PROJECT_NAME

# 🚀 FLAG ÚNICO: Cambia aquí para staging/production
ENV_MODE = os.getenv("ENV_MODE", "staging")  # "staging" o "production"

# Lista de orígenes permitidos
ALLOWED_ORIGINS = {
    "production": [
        "https://cx-frontendnew.vercel.app",  # Solo producción
    ],
    "staging": [
        "https://cx-frontendnew.vercel.app",
        "http://localhost:3000",
        "http://localhost:4200",
        "https://15822175-65a6-4121-98ff-cebb930d073a.preview.emergentagent.com",
    ]
}

# Wildcards para staging (Vercel previews)
STAGING_WILDCARDS = [
    "vercel.app",
    "emergentagent.com",
    "localhost"
]

# Middleware CORS universal
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    
    # Verificar origen
    if is_allowed(origin):
        response = await call_next(request)
        response.headers.update({
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
        })
        return response
    
    # Preflight OPTIONS
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    return await call_next(request)

def is_allowed(origin: str) -> bool:
    """Verifica origen según ENV_MODE"""
    if ENV_MODE == "production":
        return origin in ALLOWED_ORIGINS["production"]
    else:  # staging/development
        # Orígenes exactos
        if origin in ALLOWED_ORIGINS["staging"]:
            return True
        # Wildcards Vercel/localhost
        return any(wildcard in origin for wildcard in STAGING_WILDCARDS)

# Routing
app.include_router(api_router, prefix=settings.API_URL)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "env_mode": ENV_MODE,  # Para debug
        "allowed_origins": ALLOWED_ORIGINS.get(ENV_MODE, [])
    }
