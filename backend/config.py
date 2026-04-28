from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    deepseek_api_key: str = "sk-placeholder"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    chat_model: str = "deepseek-chat"
    reasoner_model: str = "deepseek-reasoner"

    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chroma_persist_dir: str = "./rag/chroma_db"
    rag_top_k: int = 4

    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
