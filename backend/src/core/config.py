from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    JWT_SECRET: str = Field(..., min_length=8, description="Secret for signing JWT")
    JWT_EXPIRES_HOURS: int = 12
    TZ: str = "America/Sao_Paulo"
    CORS_ORIGINS: str = "http://localhost:5173"
    ENV: str = "dev"
    SENTRY_DSN_BACKEND: str = ""
    APP_VERSION: str = "0.1.0"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in {"dev", "prod", "test"}:
            raise ValueError("ENV must be one of: dev, prod, test")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
