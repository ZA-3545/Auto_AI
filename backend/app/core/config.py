from functools import lru_cache
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _is_deployed() -> bool:
    """True on Railway/Render/production — platform env must not be overwritten by .env."""
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
        return True
    return os.getenv("ENVIRONMENT", "").strip().lower() == "production"


def _apply_dotenv_overrides() -> None:
    """Local dev only: load backend/.env into the process."""
    if _is_deployed():
        return
    values = dotenv_values(_BACKEND_DIR / ".env")
    for name, value in values.items():
        if name and value is not None:
            os.environ[name] = value.strip().strip('"').strip("'")


_apply_dotenv_overrides()


def database_url_looks_local(url: str) -> bool:
    lowered = url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered


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

    # Comma-separated frontend origins for CORS (fully env-driven).
    # Local default below; in production set CORS_ORIGINS to your Vercel URL(s).
    # Code also allows https://*.vercel.app via regex. Use * to allow all origins.
    # CORS_ORIGINS=https://auto-ai-black.vercel.app,http://localhost:3000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # PostgreSQL connection URL (sync — SQLAlchemy / Alembic / scripts).
    # Local example: postgresql+psycopg2://user:password@127.0.0.1:5433/autoai
    # Managed hosts often give postgres:// or postgresql:// — normalized below.
    # Append ?sslmode=require when the provider requires TLS.
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/autoai"

    # Async URL (reserved for async sessions). Same host notes as DATABASE_URL.
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

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_sync_database_url(cls, value: object) -> object:
        """Accept managed-host URLs (postgres://) and prefer psycopg2 driver."""
        if not isinstance(value, str) or not value.strip():
            return value
        url = value.strip().strip('"').strip("'")
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+psycopg2://" not in url and "+psycopg://" not in url:
            url = "postgresql+psycopg2://" + url[len("postgresql://") :]
        return url

    @field_validator("DATABASE_URL_ASYNC", mode="before")
    @classmethod
    def _normalize_async_database_url(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            return value
        url = value.strip().strip('"').strip("'")
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+asyncpg://" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        return url

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
        if _is_deployed():
            # Railway/Render dashboard vars must win over any baked-in .env file.
            return init_settings, env_settings, dotenv_settings, file_secret_settings
        # Local: backend/.env wins over inherited process env (Cursor injects OPENAI_API_KEY).
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
