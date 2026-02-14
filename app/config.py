from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()

class Settings(BaseModel):
    # Vertex config
    vertex_project: str = os.getenv("VERTEX_PROJECT", "")
    vertex_location: str = os.getenv("VERTEX_LOCATION", "us-central1")

    # Choose models via env
    vertex_model: str = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
    vertex_embedding_model: str = os.getenv("VERTEX_EMBED_MODEL", "text-embedding-005")

    # Data paths
    raw_data_dir: str = os.getenv("RAW_DATA_DIR", "./data/raw")
    index_dir: str = os.getenv("INDEX_DIR", "./data/index")
    log_dir: str = os.getenv("LOG_DIR", "./data/logs")

    # Retrieval params
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    top_k: int = int(os.getenv("TOP_K", "6"))

settings = Settings()