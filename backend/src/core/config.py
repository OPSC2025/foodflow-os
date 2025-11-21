"""
Core configuration module for FoodFlow OS.

Uses Pydantic Settings for environment-based configuration with validation.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables with the prefix APP_.
    Example: APP_DATABASE_URL=postgresql://...
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "FoodFlow OS"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # API
    api_v1_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    # Security
    secret_key: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_USE_LONG_RANDOM_STRING",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    
    # Database - PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://foodflow:foodflow@localhost:5432/foodflow",
        description="PostgreSQL connection URL for async operations",
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    database_echo: bool = False
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_pool_size: int = 10
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # Multi-Tenancy
    tenant_schema_prefix: str = "tenant_"
    shared_schema_name: str = "public"
    
    # Event Bus (will be Redpanda/Kafka later, using PostgreSQL outbox for now)
    event_bus_enabled: bool = True
    event_bus_poll_interval: int = 5  # seconds
    
    # AI/ML - OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for LLM")
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 4000
    
    # Copilot Configuration
    copilot_conversation_history_limit: int = Field(
        default=10,
        description="Maximum number of messages to keep in conversation context",
    )
    copilot_max_tool_retries: int = Field(
        default=2,
        description="Maximum retries for failed tool executions",
    )
    copilot_timeout_seconds: float = Field(
        default=60.0,
        description="Maximum time for Copilot response generation",
    )
    copilot_max_tool_iterations: int = Field(
        default=5,
        description="Maximum number of tool calling iterations per request",
    )
    
    # Feature Store
    feature_store_enabled: bool = True
    feature_store_cache_ttl: int = 300  # seconds
    
    # ML Model Serving
    model_serving_enabled: bool = True
    model_registry_path: str = "./models"
    
    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = False
    metrics_port: int = 9090
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 100
    
    # Celery (Background Tasks)
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )
    
    # AI Service
    ai_service_url: str = Field(
        default="http://localhost:8001",
        description="AI service base URL",
    )
    ai_service_timeout_seconds: int = Field(
        default=30,
        description="AI service request timeout in seconds",
    )
    ai_service_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for AI service calls",
    )
    ai_service_retry_delay_seconds: float = Field(
        default=1.0,
        description="Initial delay between AI service retries (exponential backoff)",
    )
    
    # Test Database
    test_database_url: Optional[str] = Field(
        default=None,
        description="Test database URL (defaults to database_url with _test suffix)",
    )
    
    @property
    def get_test_database_url(self) -> str:
        """Get test database URL, creating it from main URL if not specified."""
        if self.test_database_url:
            return self.test_database_url
        # Replace database name with _test suffix
        import re
        return re.sub(r'/(\w+)$', r'/\1_test', self.database_url)
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_database_url_for_tenant(self, tenant_schema: str) -> str:
        """
        Get database URL with tenant schema set in search_path.
        
        Args:
            tenant_schema: The tenant's schema name
            
        Returns:
            Database URL string
        """
        return f"{self.database_url}?options=-c%20search_path={tenant_schema}"
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get structured logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if self.is_production else "standard",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sqlalchemy": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure settings are loaded only once.
    
    Returns:
        Settings instance
    """
    return Settings()


# Convenience export
settings = get_settings()
