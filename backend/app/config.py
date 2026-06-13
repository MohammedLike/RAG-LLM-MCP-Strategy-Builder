import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://quant_user:quant_password@localhost:5432/quant_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL_NAME: str = "deepseek-r1:8b"
    EMBEDDING_MODEL_NAME: str = "mxbai-embed-large"
    
    # Market Data
    MARKET_DATA_PROVIDER: str = "yfinance" # nse, yfinance, broker
    OHLCV_DB_ONLY: bool = True  # when True, backtests use Postgres ohlcv only (no yfinance fallback)
    
    # Broker API (Optional)
    BROKER_API_KEY: str | None = None
    BROKER_API_SECRET: str | None = None
    BROKER_ACCESS_TOKEN: str | None = None

settings = Settings()
