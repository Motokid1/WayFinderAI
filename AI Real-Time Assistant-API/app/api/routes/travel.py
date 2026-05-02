from fastapi import APIRouter, HTTPException

from app.schemas.travel import TravelPlanRequest, TravelPlanResponse
from app.graph.travel_graph import run_travel_planner_agent
from app.tools.tool_registry import TRAVEL_TOOLS

# ============================================================
# RAG ingestion disabled for Render Free deployment.
# Do not delete this import.
# Uncomment this only in the full RAG-enabled branch/deployment.
# ============================================================

# from app.rag.ingest_city_guides import ingest_city_guides


router = APIRouter()


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
            "local_trends": result.get("local_trends", []),

            "itinerary": result.get("itinerary", {}),
            "food_suggestions": result.get("food_suggestions", []),
            "travel_tips": result.get("travel_tips", []),
            "safety_tips": result.get("safety_tips", []),

            "budget_warning": result.get("budget_warning", ""),
            "data_limitations": result.get("data_limitations", []),

            "final_summary": result.get("final_summary", ""),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Travel planning failed: {str(e)}",
        )


# ============================================================
# RAG ingestion endpoint disabled for Render Free deployment.
# Do not delete this block.
# Uncomment this only in the full RAG-enabled branch/deployment.
# ============================================================

# @router.post("/ingest-city-guides")
# def ingest_guides():
#     try:
#         result = ingest_city_guides()
#         return result
#
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