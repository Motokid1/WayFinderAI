from app.rag.vectorstore import get_vectorstore


def retrieve_city_guide(
    destination: str,
    query: str,
    interests: list[str] | None = None,
    food_preference: str | None = None,
    travel_style: str | None = None,
    k: int = 8,
) -> str:
    vectorstore = get_vectorstore()

    interests = interests or []
    interests_text = ", ".join(interests) if interests else "general travel"

    search_query = f"""
    Destination: {destination}
    User interests: {interests_text}
    Food preference: {food_preference}
    Travel style: {travel_style}

    Retrieve content that directly matches these interests:
    {interests_text}

    Important:
    If interests include nightlife, clubs, pubs, bars, lounges, cafes, or parties,
    retrieve only nightlife/cafe/evening travel sections, nightlife zones,
    safety tips, late-night transport, and budget notes.

    Do not prioritize generic sightseeing unless the user asked for it.

    User query:
    {query}
    """

    docs = vectorstore.similarity_search(
        search_query,
        k=k,
        filter={"city": destination.lower()},
    )

    if not docs:
        return f"""
    No stored RAG city guide was found for {destination}.

    This destination is not currently available in the local city guide knowledge base.

    Use discovered places, weather, budget, news, and risk outputs if available.
    Do not pretend that city guide data exists for this destination.
    """

    return "\n\n".join([doc.page_content for doc in docs])