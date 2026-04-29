from typing import TypedDict, List, Dict, Any, Optional


class TravelGraphState(TypedDict, total=False):
    destination: str
    days: int
    travelers: int
    budget: int
    travel_style: str
    food_preference: str
    source_city: Optional[str]
    interests: List[str]

    news_required: bool
    news_limit: int
    risk_check: bool

    weather_needed: bool
    city_guide_needed: bool
    places_needed: bool
    budget_needed: bool
    news_needed: bool
    news_analysis_needed: bool
    risk_needed: bool

    weather_summary: Dict[str, Any]
    city_guide_context: str

    places_result: Dict[str, Any]
    discovered_places: List[Dict[str, Any]]

    cost_breakdown: Dict[str, Any]

    news_articles: List[Dict[str, Any]]
    news_summary: str
    news_sentiment: str
    travel_risk: Dict[str, Any]
    local_trends: List[str]

    itinerary: Dict[str, List[str]]
    food_suggestions: List[str]
    travel_tips: List[str]
    safety_tips: List[str]

    budget_warning: str
    data_limitations: List[str]

    final_summary: str
    executed_nodes: List[str]
    error: Optional[str]