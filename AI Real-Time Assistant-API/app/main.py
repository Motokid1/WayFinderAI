from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes.health import router as health_router
from app.api.routes.travel import router as travel_router


settings = get_settings()


def build_allowed_origins() -> list[str]:
    """
    Builds the list of allowed frontend origins for CORS.

    FRONTEND_URL is loaded from .env or Render environment variables.
    """

    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    frontend_url = settings.FRONTEND_URL.strip() if settings.FRONTEND_URL else ""

    if frontend_url and frontend_url not in default_origins:
        default_origins.append(frontend_url)

    return default_origins


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["Health"],
)

app.include_router(
    travel_router,
    prefix="/api/v1/travel",
    tags=["Travel"],
)


@app.get("/")
def root():
    return {
        "message": "WayFinder Backend is running",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "frontend_url": settings.FRONTEND_URL,
        "allowed_origins": build_allowed_origins(),
    }