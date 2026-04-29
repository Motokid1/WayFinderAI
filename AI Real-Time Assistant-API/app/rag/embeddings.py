from functools import lru_cache
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )