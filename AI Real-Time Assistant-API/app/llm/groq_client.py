from functools import lru_cache
from langchain_groq import ChatGroq

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_llm():
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL_NAME,
        temperature=0.2,
    )