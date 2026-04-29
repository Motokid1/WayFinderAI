from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TravelPlanRequest(BaseModel):
    destination: str = Field(..., example="Pune")
    days: int = Field(..., ge=1, le=15, example=2)
    travelers: int = Field(default=1, ge=1, le=20, example=1)
    budget: int = Field(..., ge=500, example=12000)
    travel_style: str = Field(default="comfort", example="comfort")
    food_preference: str = Field(default="mixed", example="mixed")
    source_city: Optional[str] = Field(default=None, example="Vijayawada")
    interests: Optional[List[str]] = Field(
        default_factory=list,
        example=["clubs", "pubs", "cafes", "nightlife"],
    )

    news_required: bool = Field(default=True, example=True)
    news_limit: int = Field(default=5, ge=1, le=10, example=5)
    risk_check: bool = Field(default=True, example=True)


class TravelPlanResponse(BaseModel):
    destination: str
    days: int
    travelers: int
    budget: int
    travel_style: str
    food_preference: str

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

    budget_warning: str = ""
    data_limitations: List[str] = []

    final_summary: str