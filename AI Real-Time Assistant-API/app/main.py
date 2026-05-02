from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes.health import router as health_router
from app.api.routes.travel import router as travel_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://wayfinderai-ui.onrender.com/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(travel_router, prefix="/api/v1", tags=["Travel"])


@app.get("/")
def root():
    return {
        "message": "WayFinder Backend is running",
        "version": settings.APP_VERSION,
    }