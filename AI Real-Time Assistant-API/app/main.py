from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.langsmith import configure_langsmith
from app.api.routes.health import router as health_router
from app.api.routes.travel import router as travel_router

settings = get_settings()
configure_logging()
configure_langsmith()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Real-Time Life Assistant Backend - Checkpoint 2 News-Aware Travel Planner",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(travel_router, prefix="/api/v1/travel", tags=["Travel Planner"])


@app.get("/")
def root():
    return {
        "message": "AI Real-Time Life Assistant Backend is running",
        "checkpoint": "Checkpoint 2 - News-Aware AI Travel Planner Agent",
        "langsmith_project": settings.LANGSMITH_PROJECT,
        "docs": "/docs",
    }