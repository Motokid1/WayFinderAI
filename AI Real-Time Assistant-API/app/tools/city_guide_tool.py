from langchain_core.tools import tool
from langsmith import traceable

from app.rag.retriever import retrieve_city_guide


@tool
@traceable(name="city_guide_rag_tool")
def city_guide_rag_tool(
    destination: str,
    user_query: str,
    interests: list[str] | None = None,
    food_preference: str | None = None,
    travel_style: str | None = None,
) -> str:
    """
    Retrieve interest-aware city guide context from the local RAG vector database.

    Args:
        destination: Destination city name.
        user_query: User's travel planning query.
        interests: User interests such as nightlife, clubs, pubs, shopping, history, food, cafes.
        food_preference: User's food preference.
        travel_style: User's travel style.

    Returns:
        Relevant city guide context based on the user's specific interests.
    """

    return retrieve_city_guide(
        destination=destination,
        query=user_query,
        interests=interests,
        food_preference=food_preference,
        travel_style=travel_style,
        k=6,
    )