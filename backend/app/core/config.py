from functools import lru_cache
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _apply_dotenv_overrides() -> None:
    """Force backend/.env values into the process, replacing inherited keys."""
    values = dotenv_values(_BACKEND_DIR / ".env")
    for name, value in values.items():
        if name and value is not None:
            os.environ[name] = value.strip().strip('"').strip("'")


_apply_dotenv_overrides()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AutoAI API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Comma-separated list of allowed CORS origins
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # PostgreSQL connection URL
    # Example: postgresql+psycopg2://user:password@localhost:5432/autoai
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/autoai"

    # Async URL used when async SQLAlchemy sessions are needed later
    # Example: postgresql+asyncpg://user:password@localhost:5432/autoai
    DATABASE_URL_ASYNC: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/autoai"
    )

    # AI provider abstraction (PLANNING.md Section B.4)
    # Supported: openai, openrouter
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Embeddings for RAG knowledge retrieval (Phase 6)
    # OpenAI: text-embedding-3-small | OpenRouter: openai/text-embedding-3-small
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_TOP_K: int = 4
    RAG_MIN_SIMILARITY: float = 0.28

    # Phase 8 — reliability / privacy / ops
    RATE_LIMIT_PER_MINUTE: int = 30
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_BACKOFF_SECONDS: float = 0.6
    LLM_TIMEOUT_SECONDS: float = 45.0
    CONVERSATION_RETENTION_DAYS: int = 30

    @field_validator("OPENAI_API_KEY", "OPENROUTER_API_KEY", mode="before")
    @classmethod
    def _strip_api_key(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value

    @property
    def embedding_model_resolved(self) -> str:
        """Normalize embedding model id for the active provider."""
        model = (self.EMBEDDING_MODEL or "text-embedding-3-small").strip()
        if self.AI_PROVIDER == "openrouter" and "/" not in model:
            return f"openai/{model}"
        return model

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # backend/.env must win over inherited process env (Cursor injects OPENAI_API_KEY).
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
