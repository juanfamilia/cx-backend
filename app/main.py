from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI(docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.title = settings.PROJECT_NAME

# 🚨 CORS MIDDLEWARE PRIMERO (antes de cualquier ruta)
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    
    # OPTIONS preflight SIEMPRE 200
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",  # 24h cache
            }
        )
    
    # Verificar origen para métodos reales
    if origin and not is_allowed(origin):
        return JSONResponse(
            status_code=403,
            content={"detail": "CORS origin not allowed"},
            headers={"Access-Control-Allow-Origin": origin}
        )
    
    # Procesar request normal + agregar CORS headers
    response = await call_next(request)
    response.headers.update({
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    })
    return response

def is_allowed(origin: str) -> bool:
    ENV_MODE = os.getenv("ENV_MODE", "staging")
    ALLOWED_ORIGINS = {
        "production": ["https://cx-frontendnew.vercel.app"],
        "staging": ["https://cx-frontendnew.vercel.app", "http://localhost:3000", "http://localhost:4200"]
    }
    STAGING_WILDCARDS = ["vercel.app", "emergentagent.com", "localhost"]
    
    origins_list = ALLOWED_ORIGINS.get(ENV_MODE, [])
    if origin in origins_list:
        return True
    return ENV_MODE != "production" and any(w in origin for w in STAGING_WILDCARDS)

# ✨ RUTAS DESPUÉS del middleware
app.include_router(api_router, prefix=settings.API_URL)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "cors": "fixed"}
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI(docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.title = settings.PROJECT_NAME

# 🚨 CORS MIDDLEWARE PRIMERO (antes de cualquier ruta)
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    
    # OPTIONS preflight SIEMPRE 200
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",  # 24h cache
            }
        )
    
    # Verificar origen para métodos reales
    if origin and not is_allowed(origin):
        return JSONResponse(
            status_code=403,
            content={"detail": "CORS origin not allowed"},
            headers={"Access-Control-Allow-Origin": origin}
        )
    
    # Procesar request normal + agregar CORS headers
    response = await call_next(request)
    response.headers.update({
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    })
    return response

def is_allowed(origin: str) -> bool:
    ENV_MODE = os.getenv("ENV_MODE", "staging")
    ALLOWED_ORIGINS = {
        "production": ["https://cx-frontendnew.vercel.app"],
        "staging": ["https://cx-frontendnew.vercel.app", "http://localhost:3000", "http://localhost:4200"]
    }
    STAGING_WILDCARDS = ["vercel.app", "emergentagent.com", "localhost"]
    
    origins_list = ALLOWED_ORIGINS.get(ENV_MODE, [])
    if origin in origins_list:
        return True
    return ENV_MODE != "production" and any(w in origin for w in STAGING_WILDCARDS)

# ✨ RUTAS DESPUÉS del middleware
app.include_router(api_router, prefix=settings.API_URL)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "cors": "fixed"}
