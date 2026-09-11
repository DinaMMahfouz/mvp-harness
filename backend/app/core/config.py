"""Application settings, read from environment variables / .env file.

Never hardcode secrets here — everything comes from the process environment
(Render/Vercel dashboards in prod, local .env in dev, which is gitignored).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_psycopg3_driver(cls, v: str) -> str:
        """Normalize plain postgresql:// URLs to the psycopg3 dialect we install.

        Supabase and most docs hand out bare postgresql:// connection strings;
        SQLAlchemy would otherwise default to psycopg2, which we don't depend on.
        """
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    ANTHROPIC_API_KEY: str = ""

    N8N_WEBHOOK_URL: str = ""
    HARNESS_WEBHOOK_SECRET: str = ""

    CORS_ORIGINS: str = "http://localhost:5173"

    ENV: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
