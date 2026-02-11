from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SmartBets Pro API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://smartbets:smartbets@localhost:5432/smartbets"
    database_url_sync: str = "postgresql://smartbets:smartbets@localhost:5432/smartbets"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    admin_token: str = "dev-admin-token"

    # Data providers (real API keys - TODO for production)
    odds_api_key: str = ""
    stats_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Model
    model_version: str = "v1.0"
    default_min_edge: float = 2.0
    default_min_prob: float = 0.05

    # Jobs
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    model_config = {"env_prefix": "SMARTBETS_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
