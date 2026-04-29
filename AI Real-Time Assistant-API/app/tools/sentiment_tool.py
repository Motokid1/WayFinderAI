from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langsmith import traceable

from app.llm.groq_client import get_llm


@tool
@traceable(name="news_sentiment_tool")
def news_sentiment_tool(news_summary: str) -> str:
    """
    Analyze the overall sentiment of destination news.

    Args:
        news_summary: Summarized destination news.

    Returns:
        One of: Positive, Neutral, Negative, Mixed.
    """

    if not news_summary or news_summary.strip() == "":
        return "Neutral"

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        You are a travel news sentiment classifier.

        Classify the overall sentiment of this destination news.

        News Summary:
        {news_summary}

        Return only one word:
        Positive, Neutral, Negative, Mixed
        """
    )

    chain = prompt | llm
    response = chain.invoke({"news_summary": news_summary})

    sentiment = response.content.strip()

    allowed = ["Positive", "Neutral", "Negative", "Mixed"]

    for item in allowed:
        if item.lower() in sentiment.lower():
            return item

    return "Neutral"