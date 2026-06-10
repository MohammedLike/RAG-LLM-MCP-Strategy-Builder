import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://quant_user:quant_password@localhost:5432/quant_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL_NAME: str = "mistral:instruct"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    
    # Market Data
    MARKET_DATA_PROVIDER: str = "yfinance" # nse, yfinance, broker
    
    # Broker API (Optional)
    BROKER_API_KEY: str | None = None
    BROKER_API_SECRET: str | None = None
    BROKER_ACCESS_TOKEN: str | None = None

    class Config:
        env_file = "../.env"

settings = Settings()
