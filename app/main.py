from fastapi import FastAPI
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

# 🔥 DEBUG: imprime rutas cargadas
@app.on_event("startup")
async def print_routes():
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        print(route.path)
    print("=========================\n")

# Routing principal
app.include_router(api_router, prefix=settings.API_URL)

# Health check
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "healthy", "service": "siete-cx-api"}
    )

# Root para evitar 404 en /
@app.get("/")
def root():
    return {"message": "API running"}
