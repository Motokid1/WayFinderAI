import json
import re
from datetime import datetime, timezone
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langsmith import traceable

from app.llm.groq_client import get_llm
from app.core.database import get_travel_risk_logs_collection


@tool
@traceable(name="travel_risk_tool")
def travel_risk_tool(
    destination: str,
    news_summary: str,
    weather_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze travel risk based on destination news and weather.

    Args:
        destination: Destination city name.
        news_summary: Summarized destination news.
        weather_summary: Current weather summary.

    Returns:
        Risk analysis with risk_level, reason, and risk_factors.
    """

    if not news_summary:
        return {
            "risk_level": "Low",
            "reason": "No major news risk found.",
            "risk_factors": [],
        }

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        You are a travel risk analyzer.

        Destination:
        {destination}

        News Summary:
        {news_summary}

        Weather Summary:
        {weather_summary}

        Risk Rules:
        Low:
        - Normal news
        - No alerts
        - No major disruption

        Medium:
        - Heavy traffic
        - Rain warnings
        - Local crowding
        - Minor protests

        High:
        - Floods
        - Riots
        - Serious safety incidents
        - Travel restrictions
        - Natural disasters

        Return valid JSON only:

        {{
          "risk_level": "Low | Medium | High",
          "reason": "short reason",
          "risk_factors": ["factor 1", "factor 2"]
        }}
        """
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "destination": destination,
            "news_summary": news_summary,
            "weather_summary": json.dumps(weather_summary, indent=2),
        }
    )

    parsed = extract_json_from_llm_response(response.content)

    save_risk_log(destination, parsed)

    return parsed


@traceable(name="extract_risk_json")
def extract_json_from_llm_response(content: str) -> Dict[str, Any]:
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

    return {
        "risk_level": "Low",
        "reason": "Unable to parse risk output. Defaulting to low risk.",
        "risk_factors": [],
    }


@traceable(name="save_risk_log")
def save_risk_log(destination: str, risk_result: Dict[str, Any]) -> None:
    try:
        collection = get_travel_risk_logs_collection()

        collection.insert_one(
            {
                "destination": destination.lower(),
                "risk_result": risk_result,
                "created_at": datetime.now(timezone.utc),
            }
        )

    except Exception:
        pass