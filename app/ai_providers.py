from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from .config import settings


def get_llm() -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI
    if not settings.vertex_project:
        raise RuntimeError("Missing VERTEX_PROJECT")
    return ChatGoogleGenerativeAI(
        model=settings.vertex_model,
        temperature=0.2,
    )

def get_embeddings() -> Embeddings:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    if not settings.vertex_project:
        raise RuntimeError("Missing VERTEX_PROJECT")
    return GoogleGenerativeAIEmbeddings(
        model=settings.vertex_embedding_model,
        google_cloud_project=settings.vertex_project,
        location=settings.vertex_location,
    )