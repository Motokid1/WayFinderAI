from app.tools.weather_tool import weather_tool
from app.tools.budget_tool import budget_estimator_tool
from app.tools.city_guide_tool import city_guide_rag_tool
from app.tools.places_tool import places_discovery_tool
from app.tools.news_tool import news_fetch_tool
from app.tools.sentiment_tool import news_sentiment_tool
from app.tools.risk_analyzer import travel_risk_tool
from app.tools.trend_tool import local_trend_tool


TRAVEL_TOOLS = [
    weather_tool,
    budget_estimator_tool,
    city_guide_rag_tool,
    places_discovery_tool,
    news_fetch_tool,
    news_sentiment_tool,
    travel_risk_tool,
    local_trend_tool,
]