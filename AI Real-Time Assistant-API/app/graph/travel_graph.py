import json
import re
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from app.graph.state import TravelGraphState

from app.tools.weather_tool import weather_tool
from app.tools.budget_tool import budget_estimator_tool
from app.tools.city_guide_tool import city_guide_rag_tool
from app.tools.places_tool import places_discovery_tool
from app.tools.news_tool import news_fetch_tool
from app.tools.sentiment_tool import news_sentiment_tool
from app.tools.risk_analyzer import travel_risk_tool
from app.tools.trend_tool import local_trend_tool

from app.llm.groq_client import get_llm
from app.prompts.travel_prompt import TRAVEL_PLANNER_PROMPT
from app.core.database import get_news_analysis_history_collection


ROUTER_PROMPT = """
You are a routing node inside a LangGraph travel planner.

The user has already submitted structured travel data.

Your job is ONLY to decide which tools are required.

Input:
Destination: {destination}
Days: {days}
Budget: {budget}
Travel Style: {travel_style}
Food Preference: {food_preference}
Interests: {interests}
News Required: {news_required}
Risk Check: {risk_check}

Tool decision rules:
1. For a travel plan, weather is usually needed.
2. For a travel plan, city guide RAG is usually needed.
3. If user interests require real places such as clubs, pubs, cafes, restaurants, malls, hospitals, museums, attractions, beaches, nightlife, or shopping:
   - places_needed=true
4. If budget is provided, budget estimation is needed.
5. If news_required is true, news is needed.
6. If news is needed, news analysis is needed.
7. If risk_check is true, risk analysis is needed.
8. If interests include clubs, pubs, bars, parties, nightlife, late-night food, events, or concerts:
   - city_guide_needed=true
   - places_needed=true
   - budget_needed=true
   - news_needed=true
   - news_analysis_needed=true
   - risk_needed=true
9. If interests include safety, traffic, news, protest, events, or local updates:
   - news_needed=true
   - risk_needed=true

Return valid JSON only.

JSON format:
{
  "weather_needed": true,
  "city_guide_needed": true,
  "places_needed": true,
  "budget_needed": true,
  "news_needed": true,
  "news_analysis_needed": true,
  "risk_needed": true
}
"""


def default_router_decision(state: TravelGraphState) -> dict:
    news_required = state.get("news_required", True)
    risk_check = state.get("risk_check", True)

    return {
        "weather_needed": True,
        "city_guide_needed": True,
        "places_needed": True,
        "budget_needed": True,
        "news_needed": news_required,
        "news_analysis_needed": news_required,
        "risk_needed": risk_check,
    }


@traceable(name="router_node")
def router_node(state: TravelGraphState) -> TravelGraphState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "destination": state["destination"],
                "days": state["days"],
                "budget": state["budget"],
                "travel_style": state["travel_style"],
                "food_preference": state["food_preference"],
                "interests": state.get("interests", []),
                "news_required": state.get("news_required", True),
                "risk_check": state.get("risk_check", True),
            }
        )

        parsed = extract_json_from_llm_response(response.content)

        if not parsed:
            parsed = default_router_decision(state)

    except Exception:
        parsed = default_router_decision(state)

    return {
        **state,
        "weather_needed": parsed.get("weather_needed", True),
        "city_guide_needed": parsed.get("city_guide_needed", True),
        "places_needed": parsed.get("places_needed", True),
        "budget_needed": parsed.get("budget_needed", True),
        "news_needed": parsed.get("news_needed", state.get("news_required", True)),
        "news_analysis_needed": parsed.get(
            "news_analysis_needed",
            state.get("news_required", True),
        ),
        "risk_needed": parsed.get("risk_needed", state.get("risk_check", True)),
        "executed_nodes": ["router_node"],
    }


@traceable(name="weather_node")
def weather_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("weather_needed", True):
        return {
            **state,
            "weather_summary": {"message": "Weather tool skipped by router."},
            "executed_nodes": state.get("executed_nodes", []) + ["weather_node_skipped"],
        }

    weather_summary = weather_tool.invoke(
        {
            "destination": state["destination"],
        }
    )

    return {
        **state,
        "weather_summary": weather_summary,
        "executed_nodes": state.get("executed_nodes", []) + ["weather_node"],
    }


@traceable(name="city_guide_node")
def city_guide_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("city_guide_needed", True):
        return {
            **state,
            "city_guide_context": "City guide RAG skipped by router.",
            "executed_nodes": state.get("executed_nodes", []) + ["city_guide_node_skipped"],
        }

    interests = state.get("interests", [])

    user_query = f"""
    Plan a {state["days"]}-day trip to {state["destination"]}
    under ₹{state["budget"]}.

    Travel style: {state["travel_style"]}
    Food preference: {state["food_preference"]}
    User interests: {interests}

    Important:
    The itinerary must strongly prioritize these user interests:
    {interests}

    If interests include clubs, pubs, nightlife, bars, lounges, cafes, or parties,
    retrieve nightlife-related places, zones, evening activities, safety tips,
    late-night transport, and budget notes instead of generic tourist places.
    """

    city_guide_context = city_guide_rag_tool.invoke(
        {
            "destination": state["destination"],
            "user_query": user_query,
            "interests": interests,
            "food_preference": state.get("food_preference"),
            "travel_style": state.get("travel_style"),
        }
    )

    return {
        **state,
        "city_guide_context": city_guide_context,
        "executed_nodes": state.get("executed_nodes", []) + ["city_guide_node"],
    }


@traceable(name="places_discovery_node")
def places_discovery_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("places_needed", True):
        return {
            **state,
            "places_result": {"message": "Places discovery skipped by router."},
            "discovered_places": [],
            "executed_nodes": state.get("executed_nodes", []) + [
                "places_discovery_node_skipped"
            ],
        }

    places_result = places_discovery_tool.invoke(
        {
            "destination": state["destination"],
            "interests": state.get("interests", []),
            "limit": 12,
        }
    )

    return {
        **state,
        "places_result": places_result,
        "discovered_places": places_result.get("places", []),
        "executed_nodes": state.get("executed_nodes", []) + ["places_discovery_node"],
    }


@traceable(name="budget_node")
def budget_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("budget_needed", True):
        return {
            **state,
            "cost_breakdown": {"message": "Budget estimation skipped by router."},
            "executed_nodes": state.get("executed_nodes", []) + ["budget_node_skipped"],
        }

    cost_breakdown = budget_estimator_tool.invoke(
        {
            "destination": state["destination"],
            "days": state["days"],
            "budget": state["budget"],
            "travel_style": state["travel_style"],
            "interests": state.get("interests", []),
            "food_preference": state.get("food_preference", "mixed"),
            "travelers": state.get("travelers", 1),
            "discovered_places": state.get("discovered_places", []),
            "city_guide_context": state.get("city_guide_context", ""),
        }
    )

    return {
        **state,
        "cost_breakdown": cost_breakdown,
        "executed_nodes": state.get("executed_nodes", []) + ["budget_node"],
    }

@traceable(name="news_fetch_node")
def news_fetch_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("news_needed", True):
        return {
            **state,
            "news_articles": [],
            "news_summary": "Live news skipped by router.",
            "executed_nodes": state.get("executed_nodes", []) + [
                "news_fetch_node_skipped"
            ],
        }

    news_articles = news_fetch_tool.invoke(
        {
            "destination": state["destination"],
            "limit": state.get("news_limit", 5),
            "interests": state.get("interests", []),
        }
    )

    return {
        **state,
        "news_articles": news_articles,
        "executed_nodes": state.get("executed_nodes", []) + ["news_fetch_node"],
    }


@traceable(name="news_analysis_node")
def news_analysis_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("news_analysis_needed", True):
        return {
            **state,
            "news_summary": "News analysis skipped by router.",
            "news_sentiment": "Neutral",
            "local_trends": [],
            "executed_nodes": state.get("executed_nodes", []) + [
                "news_analysis_node_skipped"
            ],
        }

    news_articles = state.get("news_articles", [])

    if not news_articles:
        return {
            **state,
            "news_summary": "No live news articles were analyzed.",
            "news_sentiment": "Neutral",
            "local_trends": [],
            "executed_nodes": state.get("executed_nodes", []) + [
                "news_analysis_node_no_articles"
            ],
        }

    news_summary = summarize_news_for_travelers(
        destination=state["destination"],
        articles=news_articles,
        interests=state.get("interests", []),
    )

    news_sentiment = news_sentiment_tool.invoke(
        {
            "news_summary": news_summary,
        }
    )

    local_trends = local_trend_tool.invoke(
        {
            "news_summary": news_summary,
        }
    )

    save_news_analysis_history(
        destination=state["destination"],
        news_summary=news_summary,
        news_sentiment=news_sentiment,
        local_trends=local_trends,
    )

    return {
        **state,
        "news_summary": news_summary,
        "news_sentiment": news_sentiment,
        "local_trends": local_trends,
        "executed_nodes": state.get("executed_nodes", []) + ["news_analysis_node"],
    }


@traceable(name="risk_analysis_node")
def risk_analysis_node(state: TravelGraphState) -> TravelGraphState:
    if not state.get("risk_needed", True):
        return {
            **state,
            "travel_risk": {
                "risk_level": "Not Checked",
                "reason": "Risk analysis skipped by router.",
                "risk_factors": [],
            },
            "executed_nodes": state.get("executed_nodes", []) + [
                "risk_analysis_node_skipped"
            ],
        }

    travel_risk = travel_risk_tool.invoke(
        {
            "destination": state["destination"],
            "news_summary": state.get("news_summary", ""),
            "weather_summary": state.get("weather_summary", {}),
        }
    )

    return {
        **state,
        "travel_risk": travel_risk,
        "executed_nodes": state.get("executed_nodes", []) + ["risk_analysis_node"],
    }


@traceable(name="llm_planner_node")
def llm_planner_node(state: TravelGraphState) -> TravelGraphState:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(TRAVEL_PLANNER_PROMPT)
    chain = prompt | llm

    response = chain.invoke(
        {
            "destination": state["destination"],
            "days": state["days"],
            "budget": state["budget"],
            "travel_style": state["travel_style"],
            "food_preference": state["food_preference"],
            "interests": state.get("interests", []),
            "weather_summary": json.dumps(
                state.get("weather_summary", {}),
                indent=2,
                ensure_ascii=False,
            ),
            "city_guide_context": state.get("city_guide_context", ""),
            "discovered_places": json.dumps(
                state.get("discovered_places", []),
                indent=2,
                ensure_ascii=False,
            ),
            "cost_breakdown": json.dumps(
                state.get("cost_breakdown", {}),
                indent=2,
                ensure_ascii=False,
            ),
            "news_summary": state.get("news_summary", ""),
            "news_sentiment": state.get("news_sentiment", "Neutral"),
            "travel_risk": json.dumps(
                state.get("travel_risk", {}),
                indent=2,
                ensure_ascii=False,
            ),
            "local_trends": json.dumps(
                state.get("local_trends", []),
                indent=2,
                ensure_ascii=False,
            ),
        }
    )

    parsed = extract_json_from_llm_response(response.content)

    validated = validate_final_plan(
        parsed=parsed,
        state=state,
        raw_response=response.content,
    )

    return {
        **state,
        "itinerary": validated.get("itinerary", {}),
        "food_suggestions": validated.get("food_suggestions", []),
        "travel_tips": validated.get("travel_tips", []),
        "safety_tips": validated.get("safety_tips", []),
        "budget_warning": validated.get("budget_warning", ""),
        "data_limitations": validated.get("data_limitations", []),
        "final_summary": validated.get(
            "final_summary",
            "Travel plan generated successfully.",
        ),
        "executed_nodes": state.get("executed_nodes", []) + ["llm_planner_node"],
    }


@traceable(name="summarize_news_for_travelers")
def summarize_news_for_travelers(
    destination: str,
    articles: list,
    interests: list | None = None,
) -> str:
    interests = interests or []

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        You are a live news analyzer for travelers.

        Destination:
        {destination}

        User Interests:
        {interests}

        News Articles:
        {articles}

        Summarize these articles for a traveler.

        Focus on:
        - safety
        - traffic
        - weather alerts
        - protests
        - local events
        - crowding
        - travel restrictions
        - anything related to the user's interests

        If the interests include clubs, pubs, nightlife, bars, cafes, parties, or events:
        - Focus on nightlife safety
        - Late-night traffic
        - Local restrictions
        - Event crowding
        - Safe transport
        - Any relevant local updates

        Keep the summary short and practical.
        """
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "destination": destination,
            "interests": json.dumps(interests, ensure_ascii=False),
            "articles": json.dumps(articles, indent=2, ensure_ascii=False),
        }
    )

    return response.content.strip()


@traceable(name="extract_json_from_llm_response")
def extract_json_from_llm_response(content: str) -> dict:
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
            pass

    return {}


@traceable(name="validate_final_plan")
def validate_final_plan(
    parsed: dict,
    state: TravelGraphState,
    raw_response: str = "",
) -> dict:
    days = state.get("days", 1)
    interests = [str(item).lower() for item in state.get("interests", [])]
    cost_breakdown = state.get("cost_breakdown", {})
    travel_risk = state.get("travel_risk", {})
    city_guide_context = state.get("city_guide_context", "")
    discovered_places = state.get("discovered_places", [])

    itinerary = parsed.get("itinerary", {})
    food_suggestions = parsed.get("food_suggestions", [])
    travel_tips = parsed.get("travel_tips", [])
    safety_tips = parsed.get("safety_tips", [])
    budget_warning = parsed.get("budget_warning", "")
    data_limitations = parsed.get("data_limitations", [])
    final_summary = parsed.get("final_summary", "")

    repaired_itinerary = {}

    for day_number in range(1, days + 1):
        key = f"day_{day_number}"
        activities = itinerary.get(key, [])

        if not isinstance(activities, list):
            activities = []

        if len(activities) == 0:
            activities = build_fallback_day_plan(state, day_number)

        repaired_itinerary[key] = activities[:5]

    within_budget = cost_breakdown.get("within_budget")

    if within_budget is False and not budget_warning:
        estimated = cost_breakdown.get("total_estimated_cost")
        user_budget = cost_breakdown.get("user_budget") or state.get("budget")

        budget_warning = (
            f"The expected estimate is ₹{estimated}, which may exceed your planned "
            f"budget of ₹{user_budget}. Consider reducing paid activities, "
            "choosing lower-cost venues, or shortening late-night travel."
        )

    risk_level = str(travel_risk.get("risk_level", "")).lower()

    if risk_level in ["medium", "high"]:
        if not any(
            "local" in str(tip).lower() or "safe" in str(tip).lower()
            for tip in safety_tips
        ):
            safety_tips.append(
                "Review local updates before heading out and avoid poorly lit or isolated areas."
            )

    if "No stored RAG city guide was found" in city_guide_context:
        data_limitations = ensure_list(data_limitations)

        missing_message = (
            f"Stored city guide data is not available for {state.get('destination')}. "
            "The plan uses discovered places, weather, budget, news, and general safety logic."
        )

        if missing_message not in data_limitations:
            data_limitations.append(missing_message)

    if discovered_places:
        if not any("verify" in str(tip).lower() for tip in travel_tips):
            travel_tips.append(
                "Verify discovered places for current timings, entry rules, ratings, and availability before visiting."
            )

    nightlife_terms = [
        "club",
        "clubs",
        "pub",
        "pubs",
        "bar",
        "bars",
        "nightlife",
        "party",
        "parties",
        "cafe",
        "cafes",
        "lounge",
        "lounges",
    ]

    interest_text = " ".join(interests)
    has_nightlife_interest = any(term in interest_text for term in nightlife_terms)

    if has_nightlife_interest:
        generic_places = [
            "charminar",
            "golconda",
            "birla mandir",
            "mecca masjid",
            "salar jung",
            "hussain sagar",
            "qutb shahi",
            "chowmahalla",
        ]

        generic_count = 0
        all_activities = []

        for activities in repaired_itinerary.values():
            all_activities.extend([str(activity).lower() for activity in activities])

        for activity in all_activities:
            if any(place in activity for place in generic_places):
                generic_count += 1

        if generic_count >= 2:
            data_limitations = ensure_list(data_limitations)
            data_limitations.append(
                "The initial itinerary contained generic sightseeing suggestions. "
                "It was adjusted to better match nightlife, pub, club, and cafe interests."
            )

            repaired_itinerary = build_interest_focused_itinerary(state)

        if not any(
            "cab" in str(tip).lower() or "late" in str(tip).lower()
            for tip in safety_tips
        ):
            safety_tips.append(
                "Use app-based cabs for late-night travel and avoid walking through isolated areas."
            )

        if not any(
            "entry" in str(tip).lower()
            or "dress" in str(tip).lower()
            or "availability" in str(tip).lower()
            or "cover" in str(tip).lower()
            for tip in travel_tips
        ):
            travel_tips.append(
                "Check venue entry rules, dress code, age restrictions, cover charges, and table availability before visiting."
            )

    if not final_summary:
        final_summary = build_default_summary(state)

    return {
        "itinerary": repaired_itinerary,
        "food_suggestions": ensure_list(food_suggestions),
        "travel_tips": ensure_list(travel_tips),
        "safety_tips": ensure_list(safety_tips),
        "budget_warning": budget_warning,
        "data_limitations": ensure_list(data_limitations),
        "final_summary": final_summary,
    }


def ensure_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, str) and value.strip():
        return [value]

    return []


def build_default_summary(state: TravelGraphState) -> str:
    interests = state.get("interests", [])
    destination = state.get("destination", "your destination")
    days = state.get("days", 1)

    return (
        f"Your {days}-day {destination} plan has been personalized around "
        f"{', '.join(interests) if interests else 'your selected interests'}."
    )


def build_fallback_day_plan(state: TravelGraphState, day_number: int) -> list:
    interests = " ".join(state.get("interests", [])).lower()
    destination = state.get("destination", "the destination")
    discovered_places = state.get("discovered_places", [])

    place_names = [place.get("name") for place in discovered_places if place.get("name")]
    place_names = place_names[:3]

    if any(
        term in interests
        for term in [
            "club",
            "pub",
            "bar",
            "nightlife",
            "party",
            "cafe",
            "cafes",
            "lounge",
        ]
    ):
        if place_names:
            return [
                f"Afternoon: Start with a relaxed cafe or food stop near {destination}.",
                f"Evening: Consider discovered places such as {', '.join(place_names)} after verifying current details.",
                "Night: Choose one pub, lounge, cafe, or nightlife venue after checking entry rules and availability.",
                "Late night: Return using an app-based cab instead of walking or using isolated transport.",
            ]

        return [
            f"Afternoon: Keep the schedule relaxed with a cafe or dining area in {destination}.",
            "Evening: Explore a nightlife-friendly commercial area after verifying local options.",
            "Night: Choose a pub, lounge, or club only after checking current entry rules and availability.",
            "Late night: Return using an app-based cab instead of walking or using isolated transport.",
        ]

    if place_names:
        return [
            f"Morning: Visit or explore {place_names[0]} after verifying current details.",
            f"Afternoon: Continue with {place_names[1] if len(place_names) > 1 else 'a nearby food or shopping stop'}.",
            f"Evening: Keep the plan flexible around {place_names[2] if len(place_names) > 2 else 'a nearby local area'} based on weather and traffic.",
        ]

    return [
        "Morning: Start with a destination activity aligned with your selected interests.",
        "Afternoon: Choose a nearby food, shopping, or leisure stop based on your preference.",
        "Evening: Keep time flexible for local conditions, traffic, and weather.",
    ]


def build_interest_focused_itinerary(state: TravelGraphState) -> dict:
    days = state.get("days", 1)
    destination = state.get("destination", "the destination")
    discovered_places = state.get("discovered_places", [])

    place_names = [place.get("name") for place in discovered_places if place.get("name")]

    itinerary = {}

    for day_number in range(1, days + 1):
        first_place = place_names[(day_number - 1) % len(place_names)] if place_names else None
        second_place = place_names[day_number % len(place_names)] if len(place_names) > 1 else None

        evening_activity = (
            f"Evening: Consider {first_place} after verifying current timings, entry rules, and availability."
            if first_place
            else "Evening: Explore a nightlife-friendly zone from available context instead of generic sightseeing."
        )

        night_activity = (
            f"Night: Choose {second_place} or another discovered pub, lounge, club, or cafe after checking live availability."
            if second_place
            else "Night: Choose a pub, lounge, club, or cafe after checking live availability, entry rules, dress code, and cover charges."
        )

        itinerary[f"day_{day_number}"] = [
            f"Afternoon: Start with a relaxed cafe or dining area in {destination} that matches your preference.",
            evening_activity,
            night_activity,
            "Late night: Return using an app-based cab and avoid isolated areas.",
        ]

    return itinerary


@traceable(name="save_news_analysis_history")
def save_news_analysis_history(
    destination: str,
    news_summary: str,
    news_sentiment: str,
    local_trends: list,
) -> None:
    try:
        collection = get_news_analysis_history_collection()

        collection.insert_one(
            {
                "destination": destination.lower(),
                "summary": news_summary,
                "sentiment": news_sentiment,
                "local_trends": local_trends,
                "created_at": datetime.now(timezone.utc),
            }
        )

    except Exception:
        pass


def build_travel_graph():
    builder = StateGraph(TravelGraphState)

    builder.add_node("router_node", router_node)
    builder.add_node("weather_node", weather_node)
    builder.add_node("city_guide_node", city_guide_node)
    builder.add_node("places_discovery_node", places_discovery_node)
    builder.add_node("budget_node", budget_node)
    builder.add_node("news_fetch_node", news_fetch_node)
    builder.add_node("news_analysis_node", news_analysis_node)
    builder.add_node("risk_analysis_node", risk_analysis_node)
    builder.add_node("llm_planner_node", llm_planner_node)

    builder.add_edge(START, "router_node")
    builder.add_edge("router_node", "weather_node")
    builder.add_edge("weather_node", "city_guide_node")
    builder.add_edge("city_guide_node", "places_discovery_node")
    builder.add_edge("places_discovery_node", "budget_node")
    builder.add_edge("budget_node", "news_fetch_node")
    builder.add_edge("news_fetch_node", "news_analysis_node")
    builder.add_edge("news_analysis_node", "risk_analysis_node")
    builder.add_edge("risk_analysis_node", "llm_planner_node")
    builder.add_edge("llm_planner_node", END)

    return builder.compile()


travel_graph = build_travel_graph()


@traceable(name="run_travel_planner_agent")
def run_travel_planner_agent(input_data: dict) -> dict:
    initial_state: TravelGraphState = {
        "destination": input_data["destination"],
        "days": input_data["days"],
        "travelers": input_data.get("travelers", 1),
        "budget": input_data["budget"],
        "travel_style": input_data.get("travel_style", "budget friendly"),
        "food_preference": input_data.get("food_preference", "mixed"),
        "source_city": input_data.get("source_city"),
        "interests": input_data.get("interests", []),
        "news_required": input_data.get("news_required", True),
        "news_limit": input_data.get("news_limit", 5),
        "risk_check": input_data.get("risk_check", True),
    }

    final_state = travel_graph.invoke(initial_state)

    return final_state