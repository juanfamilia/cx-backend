from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Mantén original como fallback
from app.routes.main import api_router
from app.core.config import settings  # ← IMPORTA AQUÍ
import os

# Config FastAPI
app = FastAPI(
    docs_url="/docs",
    redoc_url="/redoc", 
    openapi_url="/openapi.json"
)
app.title = settings.PROJECT_NAME  # ← AHORA FUNCIONA

# 🚀 CORS MIDDLEWARE PRIMERO
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    
    # OPTIONS preflight SIEMPRE 200 OK (antes de cualquier ruta)
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            }
        )
    
    # Verificar origen solo para métodos reales
    if origin and not is_allowed_origin(origin):
        return JSONResponse(
            status_code=403,
            content={"detail": "CORS origin not allowed"},
            headers={"Access-Control-Allow-Origin": origin}
        )
    
    # Request normal + CORS headers
    response = await call_next(request)
    if origin:
        response.headers.update({
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        })
    return response

def is_allowed_origin(origin: str) -> bool:
    """Verifica origen según ENV_MODE"""
    env_mode = os.getenv("ENV_MODE", "staging")
    
    # Production: solo dominios exactos
    if env_mode == "production":
        return origin == "https://cx-frontendnew.vercel.app"
    
    # Staging: wildcards + localhost
    wildcards = ["vercel.app", "emergentagent.com", "localhost"]
    return any(wildcard in origin for wildcard in wildcards)

# ✨ RUTAS DESPUÉS del middleware
app.include_router(api_router, prefix=settings.API_URL)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "env_mode": os.getenv("ENV_MODE", "staging"),
        "cors": "fixed ✅"
    }
