# src/core/config.py
from pydantic import Field, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class AutoResolveConfig(BaseSettings):
    """
    Enterprise configuration enforcing the presence of our selected technologies.
    Fails fast on boot if any crucial infrastructure is missing.
    """

    # API Gateway
    FASTAPI_ENV: str = Field(
        default="production", description="FastAPI running environment"
    )

    # Event Broker
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        ..., description="Kafka broker address (e.g., localhost:9092)"
    )

    # Persistence
    POSTGRES_DSN: PostgresDsn = Field(..., description="PostgreSQL connection string")
    QDRANT_URL: HttpUrl = Field(..., description="Qdrant Vector DB endpoint")
    QDRANT_API_KEY: str = Field(default="", description="Qdrant API Key (if hosted)")

    # AI & Orchestration
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    LANGCHAIN_TRACING_V2: str = Field(
        default="true", description="Enable LangSmith observability"
    )

    # OLLAMA Hybrid Routing
    LLM_BACKEND: str = Field(default="local", description="Choose 'cloud' or 'local'")
    LOCAL_MODEL_NAME: str = Field(default="ollama/qwen2.5-coder:3b")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Instantiate the config so other modules can import `settings`
settings = AutoResolveConfig()
