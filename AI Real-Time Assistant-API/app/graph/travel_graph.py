import json
import re
from typing import Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langsmith import traceable

from app.graph.state import TravelGraphState
from app.llm.groq_client import get_llm
from app.tools.tool_registry import TRAVEL_TOOLS


# ============================================================
# Tool Registry Helpers
# ============================================================

TOOL_MAP = {tool.name: tool for tool in TRAVEL_TOOLS}


# ============================================================
# System Prompt for Tool-Binding Agent
# ============================================================

TOOL_BINDING_SYSTEM_PROMPT = """
You are WayFinder, a travel planning AI agent.

Use tools before creating the final plan. City-guide RAG is disabled in this deployment.
Use dynamic places, weather, budget, mobility, news if requested, and risk tools.

Rules:
- Do not invent weather, places, prices, ratings, reviews, timings, hotel names, or exact cab fares.
- For nightlife, pubs, clubs, bars, or cafes,temples, hospital, hotels or any other locations, use places and mobility tools.
- If news_required is false, avoid news tools.
- If budget is over, add budget_warning.
- Mention limitations for dynamic places and approximate transport costs.

Return only valid JSON:

{
  "itinerary": {
    "day_1": ["activity 1", "activity 2"]
  },
  "food_suggestions": [],
  "travel_tips": [],
  "safety_tips": [],
  "budget_warning": "",
  "data_limitations": [],
  "final_summary": ""
}

The itinerary must contain exactly the requested number of days.
"""

# ============================================================
# Helper Functions
# ============================================================

def safe_json_dumps(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def extract_json_from_llm_response(content: str) -> Dict[str, Any]:
    """
    Handles:
    - valid JSON
    - ```json ... ```
    - extra text before/after JSON
    """

    if not content:
        return {}

    content = content.strip()
    content = content.replace("```json", "")
    content = content.replace("```", "")
    content = content.strip()

    try:
        return json.loads(content)
    except Exception:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except Exception:
            return {}

    return {}


def ensure_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        return [value]

    return [str(value)]


def build_user_prompt(input_data: Dict[str, Any]) -> str:
    return f"""
Plan this trip using available tools.

Destination: {input_data.get("destination")}
Days: {input_data.get("days")}
Travelers: {input_data.get("travelers", 1)}
Budget INR: {input_data.get("budget")}
Travel style: {input_data.get("travel_style", "comfort")}
Food preference: {input_data.get("food_preference", "mixed")}
Source city: {input_data.get("source_city")}
Interests: {input_data.get("interests", [])}
News required: {input_data.get("news_required", False)}
News limit: {input_data.get("news_limit", 2)}
Risk check: {input_data.get("risk_check", True)}

Use dynamic places instead of RAG. Return final JSON only.
"""


def build_final_repair_prompt(
    state: TravelGraphState,
    raw_content: str,
) -> List[Any]:
    return [
        SystemMessage(
            content="""
You are a JSON repair assistant.

Convert the given travel plan content into valid JSON only.

Use this exact schema:

{
  "itinerary": {
    "day_1": [
      "activity 1",
      "activity 2",
      "activity 3"
    ]
  },
  "food_suggestions": [],
  "travel_tips": [],
  "safety_tips": [],
  "budget_warning": "",
  "data_limitations": [],
  "final_summary": ""
}

Return JSON only.
"""
        ),
        HumanMessage(
            content=f"""
Requested days: {state.get("days")}

Raw content:
{raw_content}
"""
        ),
    ]


def build_fallback_day_plan(
    state: TravelGraphState,
    day_number: int,
) -> List[str]:
    destination = state.get("destination", "the destination")
    interests = " ".join(state.get("interests", [])).lower()

    if any(
        keyword in interests
        for keyword in [
            "nightlife",
            "club",
            "clubs",
            "pub",
            "pubs",
            "bar",
            "bars",
            "cafe",
            "cafes",
        ]
    ):
        return [
            f"Morning: Keep the schedule light and review verified places around {destination}.",
            "Afternoon: Visit a cafe or food area from the discovered places if available.",
            "Evening: Choose one nightlife/cafe cluster instead of moving across distant areas.",
            "Night: Use app-based cab transport and verify venue timings before visiting.",
        ]

    return [
        f"Morning: Start with a nearby attraction or local area in {destination}.",
        "Afternoon: Plan food, cafes, or indoor activities depending on weather.",
        "Evening: Keep activities close together to reduce travel time.",
        "Night: Return safely and avoid unnecessary late-night travel.",
    ]


def build_default_summary(state: TravelGraphState) -> str:
    destination = state.get("destination", "the destination")
    days = state.get("days", 1)
    budget = state.get("budget", 0)

    return (
        f"This is a {days}-day personalized travel plan for {destination} "
        f"based on your budget of ₹{budget}, interests, available dynamic places, live tools, and safety considerations."
    )


def validate_final_plan(
    parsed: Dict[str, Any],
    state: TravelGraphState,
    raw_response: str = "",
) -> Dict[str, Any]:
    """
    Ensures final response is safe for API response model.
    Repairs missing fields.
    """

    days = int(state.get("days", 1))

    if not isinstance(parsed, dict):
        parsed = {}

    itinerary = parsed.get("itinerary", {})

    if not isinstance(itinerary, dict):
        itinerary = {}

    repaired_itinerary = {}

    for day in range(1, days + 1):
        key = f"day_{day}"
        activities = itinerary.get(key)

        if not isinstance(activities, list) or not activities:
            activities = build_fallback_day_plan(state, day)

        repaired_itinerary[key] = [str(activity) for activity in activities]

    cost_breakdown = state.get("cost_breakdown", {}) or {}
    travel_risk = state.get("travel_risk", {}) or {}
    discovered_places = state.get("discovered_places", []) or []
    stay_mobility_plan = state.get("stay_mobility_plan", {}) or {}

    budget_warning = parsed.get("budget_warning", "") or ""

    if cost_breakdown and cost_breakdown.get("within_budget") is False:
        budget_warning = (
            cost_breakdown.get("budget_note")
            or "This plan may exceed your selected budget. Reduce premium activities, long-distance transport, or paid experiences."
        )

    data_limitations = ensure_list(parsed.get("data_limitations", []))

    # ========================================================
    # RAG disabled for Render Free deployment.
    # Do not delete this block.
    # Uncomment and adjust when city guide RAG is enabled again.
    # ========================================================
    #
    # city_guide_context = state.get("city_guide_context", "") or ""
    # if "No stored RAG city guide was found" in city_guide_context:
    #     data_limitations.append(
    #         "Stored city guide data was unavailable for this destination, so the plan relies more on discovered places and live tools."
    #     )

    data_limitations.append(
        "City guide RAG is disabled for this deployment. The plan uses dynamic places, weather, budget, news, and safety tools."
    )

    if discovered_places:
        data_limitations.append(
            "Discovered places may need verification for current timings, entry rules, and availability."
        )

    if stay_mobility_plan:
        data_limitations.append(
            "Stay and transport recommendations use approximate location and distance signals; verify hotel prices and actual cab fares before booking."
        )

    if not state.get("weather_summary"):
        data_limitations.append(
            "Weather data was unavailable or limited for this destination."
        )

    risk_level = str(travel_risk.get("risk_level", "")).lower()
    safety_tips = ensure_list(parsed.get("safety_tips", []))

    if risk_level in ["medium", "high", "medium-high"]:
        safety_tips.append(
            "Because the travel risk is not low, keep the schedule flexible and avoid isolated late-night movement."
        )

    interests = " ".join(state.get("interests", [])).lower()

    if any(
        keyword in interests
        for keyword in ["nightlife", "club", "clubs", "pub", "pubs", "bar", "bars", "party"]
    ):
        safety_tips.append(
            "For nightlife plans, use app-based cabs, avoid isolated areas, and share live location with a trusted contact."
        )

    return {
        "itinerary": repaired_itinerary,
        "food_suggestions": ensure_list(parsed.get("food_suggestions", [])),
        "travel_tips": ensure_list(parsed.get("travel_tips", [])),
        "safety_tips": list(dict.fromkeys(safety_tips)),
        "budget_warning": budget_warning,
        "data_limitations": list(dict.fromkeys(data_limitations)),
        "final_summary": parsed.get("final_summary") or build_default_summary(state),
    }


def update_state_from_tool_result(
    state: TravelGraphState,
    tool_name: str,
    result: Any,
) -> TravelGraphState:
    """
    Stores known tool outputs into normal API response fields.
    This keeps your existing API response model working.
    """

    updated_state = {**state}

    if tool_name == "weather_tool":
        updated_state["weather_summary"] = (
            result if isinstance(result, dict) else {"result": result}
        )

    # ========================================================
    # RAG disabled for Render Free deployment.
    # Do not delete this block.
    # Uncomment when city_guide_rag_tool is enabled again in tool_registry.py.
    # ========================================================
    #
    # elif tool_name == "city_guide_rag_tool":
    #     updated_state["city_guide_context"] = (
    #         result if isinstance(result, str) else safe_json_dumps(result)
    #     )

    elif tool_name == "places_discovery_tool":
        updated_state["places_result"] = (
            result if isinstance(result, dict) else {"result": result}
        )

        if isinstance(result, dict):
            updated_state["discovered_places"] = result.get("places", [])

    elif tool_name == "budget_estimator_tool":
        updated_state["cost_breakdown"] = (
            result if isinstance(result, dict) else {"result": result}
        )

    elif tool_name == "news_fetch_tool":
        if isinstance(result, dict):
            updated_state["news_articles"] = result.get("articles", [])
            updated_state["news_summary"] = result.get("summary", "")
        elif isinstance(result, list):
            updated_state["news_articles"] = result
        else:
            updated_state["news_summary"] = str(result)

    elif tool_name == "news_sentiment_tool":
        if isinstance(result, dict):
            updated_state["news_sentiment"] = result.get(
                "sentiment",
                safe_json_dumps(result),
            )
        else:
            updated_state["news_sentiment"] = str(result)

    elif tool_name == "local_trend_tool":
        if isinstance(result, dict):
            trends = result.get("trends", [])
        elif isinstance(result, list):
            trends = result
        else:
            trends = [str(result)]

        normalized_trends = []

        for trend in trends:
            if isinstance(trend, str):
                normalized_trends.append(trend)

            elif isinstance(trend, dict):
                event = trend.get("event", "Local update")
                crowd = trend.get("crowd_level", "unknown crowd level")
                traffic_area = trend.get("traffic_prone_area", "unknown area")
                weather = trend.get("weather_concern", "no specific weather concern")
                transport = trend.get("recommended_transport", "local transport")
                activity = trend.get("tourist_activity", "tourist activity")

                normalized_trends.append(
                    f"{event}: Crowd level is {crowd}. "
                    f"Traffic-prone area: {traffic_area}. "
                    f"Weather concern: {weather}. "
                    f"Recommended transport: {transport}. "
                    f"Tourist activity: {activity}."
                )

            else:
                normalized_trends.append(str(trend))

        updated_state["local_trends"] = normalized_trends


    elif tool_name == "travel_risk_tool":
        updated_state["travel_risk"] = (
            result if isinstance(result, dict) else {"result": result}
        )

    elif tool_name in [
        "stay_area_discovery_tool",
        "place_clustering_tool",
        "transport_cost_tool",
        "stay_area_scoring_tool",
        "mobility_safety_tool",
    ]:
        stay_plan = updated_state.get("stay_mobility_plan", {}) or {}
        stay_plan[tool_name] = result
        updated_state["stay_mobility_plan"] = stay_plan

    else:
        tool_outputs = updated_state.get("tool_outputs", {}) or {}
        tool_outputs[tool_name] = result
        updated_state["tool_outputs"] = tool_outputs

    return updated_state


# ============================================================
# LangGraph Nodes
# ============================================================

@traceable(name="tool_binding_agent_node")
def agent_node(state: TravelGraphState) -> TravelGraphState:
    """
    LLM node with tools bound.
    The LLM decides whether to call tools or return final JSON.
    """

    llm = get_llm()
    llm_with_tools = llm.bind_tools(TRAVEL_TOOLS)

    messages = state.get("messages", [])

    response = llm_with_tools.invoke(messages)

    return {
        **state,
        "messages": messages + [response],
        "executed_nodes": state.get("executed_nodes", []) + ["agent_node"],
    }


@traceable(name="tool_executor_node")
def tool_executor_node(state: TravelGraphState) -> TravelGraphState:
    """
    Executes tool calls generated by the LLM.
    """

    messages = state.get("messages", [])

    if not messages:
        return state

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []

    if not tool_calls:
        return state

    new_messages = []
    updated_state = {**state}

    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id")

        tool = TOOL_MAP.get(tool_name)

        if not tool:
            error_payload = {
                "error": f"Tool '{tool_name}' not found.",
                "available_tools": list(TOOL_MAP.keys()),
            }

            new_messages.append(
                ToolMessage(
                    content=safe_json_dumps(error_payload),
                    tool_call_id=tool_call_id,
                )
            )
            continue

        try:
            result = tool.invoke(tool_args)

            updated_state = update_state_from_tool_result(
                state=updated_state,
                tool_name=tool_name,
                result=result,
            )

            compact_result = compact_tool_result(tool_name, result)

            new_messages.append(
                ToolMessage(
                    content=safe_json_dumps(compact_result),
                    tool_call_id=tool_call_id,
                )
            )

        except Exception as e:
            error_payload = {
                "tool": tool_name,
                "error": str(e),
            }

            new_messages.append(
                ToolMessage(
                    content=safe_json_dumps(error_payload),
                    tool_call_id=tool_call_id,
                )
            )

    return {
        **updated_state,
        "messages": messages + new_messages,
        "executed_nodes": updated_state.get("executed_nodes", []) + ["tool_executor_node"],
        "tool_call_rounds": updated_state.get("tool_call_rounds", 0) + 1,
    }


@traceable(name="final_parser_node")
def final_parser_node(state: TravelGraphState) -> TravelGraphState:
    """
    Parses final LLM JSON.
    Repairs response if needed.
    """

    messages = state.get("messages", [])

    final_content = ""

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            tool_calls = getattr(message, "tool_calls", None) or []

            if not tool_calls and message.content:
                final_content = message.content
                break

    parsed = extract_json_from_llm_response(final_content)

    if not parsed:
        llm = get_llm()
        repair_messages = build_final_repair_prompt(
            state=state,
            raw_content=final_content,
        )

        repaired_response = llm.invoke(repair_messages)
        parsed = extract_json_from_llm_response(repaired_response.content)

    final_plan = validate_final_plan(
        parsed=parsed,
        state=state,
        raw_response=final_content,
    )

    return {
        **state,
        "itinerary": final_plan["itinerary"],
        "food_suggestions": final_plan["food_suggestions"],
        "travel_tips": final_plan["travel_tips"],
        "safety_tips": final_plan["safety_tips"],
        "budget_warning": final_plan["budget_warning"],
        "data_limitations": final_plan["data_limitations"],
        "final_summary": final_plan["final_summary"],
        "executed_nodes": state.get("executed_nodes", []) + ["final_parser_node"],
    }


# ============================================================
# Conditional Routing
# ============================================================

def should_continue(state: TravelGraphState) -> str:
    messages = state.get("messages", [])

    if not messages:
        return "final_parser_node"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []

    max_rounds = state.get("max_tool_rounds", 4)
    current_rounds = state.get("tool_call_rounds", 0)

    if tool_calls and current_rounds < max_rounds:
        return "tool_executor_node"

    return "final_parser_node"


def after_tool_execution(state: TravelGraphState) -> str:
    max_rounds = state.get("max_tool_rounds", 4)
    current_rounds = state.get("tool_call_rounds", 0)

    if current_rounds >= max_rounds:
        return "final_parser_node"

    return "agent_node"


# ============================================================
# Build Graph
# ============================================================

def build_travel_graph():
    builder = StateGraph(TravelGraphState)

    builder.add_node("agent_node", agent_node)
    builder.add_node("tool_executor_node", tool_executor_node)
    builder.add_node("final_parser_node", final_parser_node)

    builder.add_edge(START, "agent_node")

    builder.add_conditional_edges(
        "agent_node",
        should_continue,
        {
            "tool_executor_node": "tool_executor_node",
            "final_parser_node": "final_parser_node",
        },
    )

    builder.add_conditional_edges(
        "tool_executor_node",
        after_tool_execution,
        {
            "agent_node": "agent_node",
            "final_parser_node": "final_parser_node",
        },
    )

    builder.add_edge("final_parser_node", END)

    return builder.compile()


travel_graph = build_travel_graph()


# ============================================================
# Public Runner
# ============================================================

@traceable(name="run_travel_planner_agent")
def run_travel_planner_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point called by FastAPI route.

    This deployment-optimized version uses:
    - LangGraph
    - LLM tool binding
    - Dynamic places
    - Stay/mobility tools
    - Weather/news/risk/budget tools

    RAG code is kept in the project but disabled from this branch.
    """

    initial_state: TravelGraphState = {
        "destination": input_data["destination"],
        "days": input_data["days"],
        "travelers": input_data.get("travelers", 1),
        "budget": input_data["budget"],
        "travel_style": input_data.get("travel_style", "comfort"),
        "food_preference": input_data.get("food_preference", "mixed"),
        "source_city": input_data.get("source_city"),
        "interests": input_data.get("interests", []),

        "news_required": input_data.get("news_required", True),
        "news_limit": input_data.get("news_limit", 2),
        "risk_check": input_data.get("risk_check", True),

        "weather_summary": {},
        "city_guide_context": (
            "City guide RAG is disabled for this deployment. "
            "This plan uses dynamic places and live tools."
        ),
        "places_result": {},
        "discovered_places": [],
        "stay_mobility_plan": {},
        "cost_breakdown": {},
        "news_articles": [],
        "news_summary": "",
        "news_sentiment": "Neutral",
        "travel_risk": {},
        "local_trends": [],

        "itinerary": {},
        "food_suggestions": [],
        "travel_tips": [],
        "safety_tips": [],
        "budget_warning": "",
        "data_limitations": [],
        "final_summary": "",

        "messages": [
            SystemMessage(content=TOOL_BINDING_SYSTEM_PROMPT),
            HumanMessage(content=build_user_prompt(input_data)),
        ],
        "tool_outputs": {},
        "executed_nodes": [],
        "tool_call_rounds": 0,

        # Render Free optimization.
        # Keep this low to avoid high latency, token usage, and memory pressure.
        "max_tool_rounds": 2,
    }

    final_state = travel_graph.invoke(initial_state)

    return final_state
def compact_tool_result(tool_name: str, result: Any) -> Any:
    """
    Reduces tool output before sending it back to the LLM.
    Full result is still stored in state, but LLM receives a smaller summary.
    """

    if not isinstance(result, dict):
        return result

    if tool_name == "places_discovery_tool":
        places = result.get("places", [])[:6]

        return {
            "destination": result.get("destination"),
            "places_found": result.get("places_found"),
            "places": [
                {
                    "name": place.get("name"),
                    "category": place.get("category"),
                    "address": place.get("address"),
                }
                for place in places
            ],
            "limitations": result.get("limitations", []),
        }

    if tool_name == "stay_area_discovery_tool":
        return {
            "destination": result.get("destination"),
            "points_found": result.get("points_found"),
            "category_counts": result.get("category_counts", {}),
            "limitations": result.get("limitations", []),
        }

    if tool_name == "place_clustering_tool":
        clusters = result.get("clusters", [])[:4]

        return {
            "clusters_found": result.get("clusters_found"),
            "clusters": [
                {
                    "cluster_id": cluster.get("cluster_id"),
                    "area_name": cluster.get("area_name"),
                    "dominant_category": cluster.get("dominant_category"),
                    "places_count": cluster.get("places_count"),
                    "planning_tip": cluster.get("planning_tip"),
                }
                for cluster in clusters
            ],
        }

    if tool_name == "news_fetch_tool":
        articles = result.get("articles", [])[:2]

        return {
            "summary": result.get("summary", ""),
            "articles": [
                {
                    "title": article.get("title"),
                    "source": article.get("source"),
                }
                for article in articles
            ],
        }

    if tool_name == "budget_estimator_tool":
        return {
            "total_estimated_cost": result.get("total_estimated_cost"),
            "total_estimate": result.get("total_estimate"),
            "category_totals": result.get("category_totals"),
            "user_budget": result.get("user_budget"),
            "within_budget": result.get("within_budget"),
            "budget_status": result.get("budget_status"),
            "budget_note": result.get("budget_note"),
            "recommendations": result.get("recommendations", [])[:3],
        }

    if tool_name == "transport_cost_tool":
        return {
            "transport_pattern": result.get("transport_pattern"),
            "estimated_total_transport_cost": result.get("estimated_total_transport_cost"),
            "budget_impact": result.get("budget_impact"),
            "daytime_strategy": result.get("daytime_strategy"),
            "late_night_plan": result.get("late_night_plan"),
        }

    if tool_name == "stay_area_scoring_tool":
        return {
            "recommended_stay_areas": result.get("recommended_stay_areas", [])[:3],
            "selection_logic": result.get("selection_logic", []),
        }

    if tool_name == "mobility_safety_tool":
        return {
            "mobility_safety_level": result.get("mobility_safety_level"),
            "reasons": result.get("reasons", []),
            "safety_rules": result.get("safety_rules", [])[:4],
        }

    if tool_name == "travel_risk_tool":
        return {
            "risk_level": result.get("risk_level"),
            "summary": result.get("summary"),
            "risk_factors": result.get("risk_factors", [])[:4],
            "recommendations": result.get("recommendations", [])[:4],
        }

    return result