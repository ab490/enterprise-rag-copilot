from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from .config import settings


def get_llm() -> BaseChatModel:
    from langchain_google_vertexai import ChatVertexAI
    if not settings.vertex_project:
        raise RuntimeError("Missing VERTEX_PROJECT")
    return ChatVertexAI(
        model=settings.vertex_model,
        project=settings.vertex_project,
        location=settings.vertex_location,
        temperature=0.2,
    )

def get_embeddings() -> Embeddings:
    from langchain_google_vertexai import VertexAIEmbeddings
    if not settings.vertex_project:
        raise RuntimeError("Missing VERTEX_PROJECT")
    return VertexAIEmbeddings(
        model_name=settings.vertex_embedding_model,
        project=settings.vertex_project,
        location=settings.vertex_location,
    )