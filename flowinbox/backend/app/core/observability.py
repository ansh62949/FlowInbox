import os
from app.core.config import settings


def setup_langsmith_observability() -> None:
    """Configures optional LangSmith tracing if API key is provided."""
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        print(f"[Observability] LangSmith tracing enabled for project: {settings.LANGSMITH_PROJECT}")
    else:
        print("[Observability] LangSmith API key unset; running normal structured logging.")
