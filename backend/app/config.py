"""
Central configuration, loaded from environment variables / .env file.

Keeping all tunables here (rather than scattered magic numbers) is what lets
the RAG pipeline's behavior -- chunk overlap, top-k, questions per session --
be adjusted without touching business logic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "all-MiniLM-L6-v2"

    database_url: str = "sqlite:///./interview_system.db"
    chroma_persist_dir: str = "./chroma_store"

    retrieval_top_k: int = 4
    questions_per_session: int = 5

    frontend_origin: str = "http://localhost:5173"

    # Valid roles supported by the system. Each must have a matching
    # ChromaDB collection name and a knowledge_base/<role>/ folder.
    supported_roles: list[str] = ["backend_engineer", "ai_ml_engineer"]


settings = Settings()
