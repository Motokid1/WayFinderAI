from app.tools.weather_tool import weather_tool
from app.tools.budget_tool import budget_estimator_tool

# ============================================================
# RAG disabled for Render Free deployment.
# Do not delete this import.
# Uncomment this only in the full RAG-enabled branch/deployment.
# ============================================================

# from app.tools.city_guide_tool import city_guide_rag_tool

from app.tools.places_tool import places_discovery_tool
from app.tools.news_tool import news_fetch_tool
from app.tools.sentiment_tool import news_sentiment_tool
from app.tools.risk_analyzer import travel_risk_tool
from app.tools.trend_tool import local_trend_tool

from app.tools.stay_mobility_tools import (
    stay_area_discovery_tool,
    place_clustering_tool,
    transport_cost_tool,
    stay_area_scoring_tool,
    mobility_safety_tool,
)


TRAVEL_TOOLS = [
    weather_tool,
    budget_estimator_tool,

    # ========================================================
    # RAG disabled for Render Free deployment.
    # Uncomment when using Chroma/HuggingFace RAG again.
    # ========================================================
    # city_guide_rag_tool,

    places_discovery_tool,
    news_fetch_tool,
    news_sentiment_tool,
    travel_risk_tool,
    local_trend_tool,

    stay_area_discovery_tool,
    place_clustering_tool,
    transport_cost_tool,
    stay_area_scoring_tool,
    mobility_safety_tool,
]