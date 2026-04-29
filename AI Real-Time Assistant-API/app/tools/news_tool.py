from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import requests
from langchain_core.tools import tool
from langsmith import traceable

from app.core.config import get_settings
from app.core.database import get_news_cache_collection

settings = get_settings()


@tool
@traceable(name="news_fetch_tool")
def news_fetch_tool(
    destination: str,
    limit: int = 5,
    interests: list[str] | None = None,
) -> list[dict]:
    """
    Fetch latest destination-related travel news.
    Interest-aware news fetching.
    """

    interests = interests or []
    interest_text = " ".join(interests).lower()

    cached_articles = get_cached_news(destination, limit)

    if cached_articles:
        return cached_articles

    queries = [
        f"{destination} travel news",
        f"{destination} traffic update",
        f"{destination} weather alert",
        f"{destination} safety news",
        f"{destination} events today",
    ]

    if any(word in interest_text for word in ["club", "clubs", "pub", "pubs", "bar", "nightlife", "party"]):
        queries.extend(
            [
                f"{destination} nightlife news",
                f"{destination} pubs clubs safety",
                f"{destination} nightlife events today",
                f"{destination} late night traffic",
            ]
        )

    all_articles = []

    for query in queries:
        articles = call_news_api(query=query, limit=limit)
        all_articles.extend(articles)

    cleaned_articles = remove_duplicate_articles(all_articles)
    limited_articles = cleaned_articles[:limit]

    save_news_to_cache(destination, limited_articles)

    return limited_articles

@traceable(name="call_news_api")
def call_news_api(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    params = {
        "q": query,
        "apiKey": settings.NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
    }

    try:
        response = requests.get(
            settings.NEWS_API_BASE_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])

        formatted_articles = []

        for article in articles:
            formatted_articles.append(
                {
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "source": article.get("source", {}).get("name"),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                }
            )

        return formatted_articles

    except Exception as e:
        return [
            {
                "title": "News unavailable",
                "description": "Unable to fetch live news at the moment.",
                "source": "system",
                "url": None,
                "published_at": None,
                "error": str(e),
            }
        ]


@traceable(name="remove_duplicate_articles")
def remove_duplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_titles = set()
    unique_articles = []

    for article in articles:
        title = article.get("title")

        if not title:
            continue

        normalized_title = title.strip().lower()

        if normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_articles.append(article)

    return unique_articles


@traceable(name="get_cached_news")
def get_cached_news(destination: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Cache validity: 2 hours.
    """

    try:
        collection = get_news_cache_collection()

        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)

        cached = collection.find_one(
            {
                "destination": destination.lower(),
                "created_at": {"$gte": two_hours_ago},
            },
            sort=[("created_at", -1)],
        )

        if cached and cached.get("articles"):
            return cached["articles"][:limit]

        return []

    except Exception:
        return []


@traceable(name="save_news_to_cache")
def save_news_to_cache(destination: str, articles: List[Dict[str, Any]]) -> None:
    try:
        collection = get_news_cache_collection()

        collection.insert_one(
            {
                "destination": destination.lower(),
                "articles": articles,
                "created_at": datetime.now(timezone.utc),
            }
        )

    except Exception:
        pass