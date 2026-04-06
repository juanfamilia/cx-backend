from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.main import api_router
from app.core.config import settings


def build_cors_origins() -> list[str]:
    """Orígenes del *frontend* (esquema + host). El host del API no debe ir aquí."""
    if settings.PROJECT_MODE == "prod":
        base = [
            "https://cx.sieteic.com",
            "https://cx-frontendnew.vercel.app",
        ]
    else:
        base = [
            "https://cx.sieteic.com",
            "https://cx-frontendnew.vercel.app",
            "http://localhost:4200",
        ]
    extra = [
        o.strip()
        for o in settings.CORS_EXTRA_ORIGINS.split(",")
        if o.strip()
    ]
    out: list[str] = []
    seen: set[str] = set()
    for o in base + extra:
        if "://" not in o:
            o = f"https://{o}"
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


# Configuración base
if settings.PROJECT_MODE == "prod":
    app = FastAPI(
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )
else:
    app = FastAPI()

app.title = settings.PROJECT_NAME

# CORS (el navegador envía Origin del sitio donde está el Angular, no el host del API)
_origins = build_cors_origins()
# Staging: sin regex en env → https://*.vercel.app (previews). Prod: solo lista explícita salvo que definas regex.
# Con CORS_ORIGIN_REGEX definido: ese patrón; tras strip vacío → solo allow_origins.
if settings.CORS_ORIGIN_REGEX is not None:
    _cors_regex: str | None = (settings.CORS_ORIGIN_REGEX or "").strip() or None
elif settings.PROJECT_MODE == "prod":
    _cors_regex = None
else:
    _cors_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=_cors_regex,
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


@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/debug/routes")
def get_routes():
    return [route.path for route in app.routes]
