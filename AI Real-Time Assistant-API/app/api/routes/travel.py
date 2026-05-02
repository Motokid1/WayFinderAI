from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.schemas.travel import TravelPlanRequest, TravelPlanResponse
from app.graph.travel_graph import run_travel_planner_agent
from app.tools.tool_registry import TRAVEL_TOOLS


router = APIRouter()


def normalize_local_trends(local_trends: Any) -> List[str]:
    """
    Ensures local_trends always returns List[str]
    because TravelPlanResponse expects local_trends: List[str].
    """

    if not local_trends:
        return []

    normalized = []

    for trend in local_trends:
        if isinstance(trend, str):
            normalized.append(trend)

        elif isinstance(trend, dict):
            event = trend.get("event", "Local update")
            crowd = trend.get("crowd_level", "unknown crowd level")
            traffic_area = trend.get("traffic_prone_area", "unknown area")
            weather = trend.get("weather_concern", "no specific weather concern")
            transport = trend.get("recommended_transport", "local transport")
            activity = trend.get("tourist_activity", "tourist activity")

            normalized.append(
                f"{event}: Crowd level is {crowd}. "
                f"Traffic-prone area: {traffic_area}. "
                f"Weather concern: {weather}. "
                f"Recommended transport: {transport}. "
                f"Tourist activity: {activity}."
            )

        else:
            normalized.append(str(trend))

    return normalized


@router.post("/plan", response_model=TravelPlanResponse)
def create_travel_plan(request: TravelPlanRequest):
    try:
        result = run_travel_planner_agent(request.model_dump())

        return {
            "destination": result.get("destination"),
            "days": result.get("days"),
            "travelers": result.get("travelers", 1),
            "budget": result.get("budget"),
            "travel_style": result.get("travel_style"),
            "food_preference": result.get("food_preference"),

            "weather_summary": result.get("weather_summary", {}),
            "city_guide_context": result.get(
                "city_guide_context",
                "City guide RAG is disabled for this deployment. This plan uses dynamic places and live tools.",
            ),

            "places_result": result.get("places_result", {}),
            "discovered_places": result.get("discovered_places", []),

            "stay_mobility_plan": result.get("stay_mobility_plan", {}),

            "cost_breakdown": result.get("cost_breakdown", {}),

            "news_articles": result.get("news_articles", []),
            "news_summary": result.get("news_summary", ""),
            "news_sentiment": result.get("news_sentiment", "Neutral"),
            "travel_risk": result.get("travel_risk", {}),

            # Important fix
            "local_trends": normalize_local_trends(result.get("local_trends", [])),

            "itinerary": result.get("itinerary", {}),
            "food_suggestions": result.get("food_suggestions", []),
            "travel_tips": result.get("travel_tips", []),
            "safety_tips": result.get("safety_tips", []),

            "budget_warning": result.get("budget_warning", ""),
            "data_limitations": result.get("data_limitations", []),

            "final_summary": result.get("final_summary", ""),
        }

    except Exception as e:
        error_text = str(e)

        if "rate_limit_exceeded" in error_text or "Rate limit reached" in error_text:
            raise HTTPException(
                status_code=429,
                detail=(
                    "The AI model daily token limit has been reached. "
                    "Please try again later, reduce trip complexity, disable news, or use a smaller model/API tier."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=f"Travel planning failed: {error_text}",
        )


# RAG ingestion disabled for Render Free deployment.
# Do not delete this block.
# Uncomment only in full RAG-enabled branch.
#
# @router.post("/ingest-city-guides")
# def ingest_guides():
#     try:
#         result = ingest_city_guides()
#         return result
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"City guide ingestion failed: {str(e)}",
#         )


@router.get("/tools")
def list_tools():
    return {
        "total_tools": len(TRAVEL_TOOLS),
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in TRAVEL_TOOLS
        ],
    }