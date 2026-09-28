from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LeadLens API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://leadlens:leadlens@localhost:5432/leadlens"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    crawl_concurrency: int = 10
    crawl_timeout_seconds: float = 10.0
    crawl_user_agent: str = (
        "LeadLensBot/0.1 (+https://github.com/azamali1144/caprae-capital-assessment)"
    )
    enrich_cache_ttl_seconds: int = 60 * 60 * 24 * 7

    llm_provider: str = "none"
    llm_api_key: str = ""
    hubspot_token: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        # lets us write CORS_ORIGINS=a,b in .env instead of a json list
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
