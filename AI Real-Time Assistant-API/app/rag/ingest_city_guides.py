import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.rag.vectorstore import get_vectorstore

settings = get_settings()


def load_city_guide_documents():
    data_dir = Path(settings.CITY_GUIDE_DATA_DIR)

    if not data_dir.exists():
        raise FileNotFoundError(f"City guide directory not found: {data_dir}")

    documents = []

    for file_path in data_dir.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        city_name = file_path.stem.lower()

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(file_path),
                    "city": city_name,
                },
            )
        )

    return documents


def ingest_city_guides():
    documents = load_city_guide_documents()

    if not documents:
        return {
            "status": "no_documents_found",
            "message": "No city guide text files found.",
        }

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    chunks = text_splitter.split_documents(documents)

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    vectorstore.persist()

    return {
        "status": "success",
        "documents_loaded": len(documents),
        "chunks_created": len(chunks),
    }


if __name__ == "__main__":
    result = ingest_city_guides()
    print(result)