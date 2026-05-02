from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "WayFinder Backend"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"

    GROQ_API_KEY: str
    LLM_MODEL_NAME: str = "llama-3.3-70b-versatile"

    WEATHER_API_KEY: str
    WEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"

    NEWS_API_KEY: str
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2/everything"

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "wayfinder_db"

    PLACES_PROVIDER: str = "openstreetmap"
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"

    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "wayfinder-travel-agent"

    # RAG kept for main branch, but optional in Render optimized branch.
    RAG_ENABLED: bool = False
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIR: str = "vector_db"
    CITY_GUIDE_DATA_DIR: str = "data/city_guides"
    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()