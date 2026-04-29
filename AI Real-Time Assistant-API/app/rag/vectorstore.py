from langchain_community.vectorstores import Chroma

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

settings = get_settings()


def get_vectorstore():
    embeddings = get_embeddings()

    vectorstore = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name="city_guides",
    )

    return vectorstore