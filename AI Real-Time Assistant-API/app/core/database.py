from functools import lru_cache
from pymongo import MongoClient

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_mongo_client():
    return MongoClient(settings.MONGODB_URI)


def get_database():
    client = get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


def get_news_cache_collection():
    db = get_database()
    return db["news_cache"]


def get_news_analysis_history_collection():
    db = get_database()
    return db["news_analysis_history"]


def get_travel_risk_logs_collection():
    db = get_database()
    return db["travel_risk_logs"]