import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langsmith import traceable

from app.llm.groq_client import get_llm


@tool
@traceable(name="local_trend_tool")
def local_trend_tool(news_summary: str) -> list:
    """
    Extract local travel trends from destination news.

    Args:
        news_summary: Summarized destination news.

    Returns:
        List of local travel trends such as crowd levels, events,
        traffic-prone areas, or recommended transport.
    """

    if not news_summary:
        return []

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        Extract useful local travel trends from the news summary.

        Focus on:
        - popular events
        - crowd levels
        - traffic-prone areas
        - weather concerns
        - recommended transport
        - tourist activity

        News Summary:
        {news_summary}

        Return valid JSON only:

        {{
          "local_trends": [
            "trend 1",
            "trend 2"
          ]
        }}
        """
    )

    chain = prompt | llm
    response = chain.invoke({"news_summary": news_summary})

    parsed = extract_json_from_llm_response(response.content)

    return parsed.get("local_trends", [])


@traceable(name="extract_local_trends_json")
def extract_json_from_llm_response(content: str) -> dict:
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
        "local_trends": []
    }