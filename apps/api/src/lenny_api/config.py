from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    web_origin: str = "http://localhost:5173"

    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_growth"
    )

    llm_provider: Literal["ollama", "anthropic"] = "ollama"
    ollama_base_url: HttpUrl = HttpUrl("http://localhost:11434")
    ollama_chat_model: str = "qwen2.5:0.5b"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = Field(default=768, ge=128, le=4096)
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str | None = None
    anthropic_max_budget_usd: float = Field(default=0.05, gt=0, le=1)
    generation_timeout_seconds: float = Field(default=90, ge=10, le=300)
    conversation_history_messages: int = Field(default=8, ge=0, le=20)

    retrieval_top_k: int = Field(default=6, ge=1, le=20)
    retrieval_score_threshold: float = Field(default=0.35, ge=0, le=1)
    transcript_source_dir: str = "data/lennys-podcast-transcripts"
    transcript_repository_url: str = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"
    chunk_target_words: int = Field(default=220, ge=80, le=500)
    chunk_overlap_words: int = Field(default=40, ge=0, le=120)

    @property
    def active_model(self) -> str:
        if self.llm_provider == "anthropic":
            return self.anthropic_model or "not-configured"
        return self.ollama_chat_model

    @property
    def cloud_configured(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
