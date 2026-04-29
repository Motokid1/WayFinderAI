import os

from app.core.config import get_settings

settings = get_settings()


def configure_langsmith():
    """
    Configures LangSmith tracing environment variables.

    LangSmith reads these environment variables automatically.
    """

    os.environ["LANGSMITH_TRACING"] = str(settings.LANGSMITH_TRACING).lower()

    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY

    if settings.LANGSMITH_PROJECT:
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT