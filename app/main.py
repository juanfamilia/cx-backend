from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.main import api_router
from app.core.config import settings

# Configuración base
if settings.PROJECT_MODE == "prod":
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
else:
    app = FastAPI()

app.title = settings.PROJECT_NAME

# CORS
if settings.PROJECT_MODE == "prod":
    origins = [
        "https://cx.sieteic.com",
        "https://cx-frontendnew.vercel.app",
    ]
else:
    origins = [
        "https://cx.sieteic.com",
        "https://cx-frontendnew.vercel.app",
        "http://localhost:4200",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router principal
app.include_router(api_router, prefix=settings.API_URL)

# Router solo para health (usa mismo prefix que la API)
health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "service": "siete-cx-api"}
    )

app.include_router(health_router, prefix=settings.API_URL)

print("🔥 ESTE MAIN SE ESTA EJECUTANDO")

@app.on_event("startup")
async def debug_routes():
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        print(route.path)
    print("=========================\n")

@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/debug/routes")
def get_routes():
    return [route.path for route in app.routes]
