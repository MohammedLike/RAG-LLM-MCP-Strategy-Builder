"""
Quant AI Agent — Application Configuration

Loads settings from environment variables / .env file using Pydantic BaseSettings.
All config is centralized here — no magic strings scattered across the codebase.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── PostgreSQL ──
    postgres_user: str = "quantagent"
    postgres_password: str = "quantagent_dev_2026"
    postgres_db: str = "quantagent"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+asyncpg://quantagent:quantagent_dev_2026@localhost:5432/quantagent"
    )

    # ── Redis ──
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    # ── Qdrant ──
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "strategies"

    # ── Ollama / LLM ──
    ollama_base_url: str = "http://localhost:11434"
    llm_model_name: str = "mistral:7b-instruct-v0.3-q4_K_M"
    temperature: float = 0.3
    max_tokens: int = 2048

    # ── Embeddings ──
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024

    # ── Market data ──
    market_data_provider: str = "yfinance"  # yfinance | nse | broker
    broker_api_key: str | None = None
    broker_api_secret: str | None = None
    broker_client_id: str | None = None

    # ── FastAPI ──
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Feature flags ──
    enable_live_market_data: bool = False
    enable_fine_tuned_model: bool = False
    log_level: str = "DEBUG"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance (cached)."""
    return Settings()
