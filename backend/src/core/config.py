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
    JWT_SECRET: str = Field(..., min_length=32, description="Secret for signing JWT (min 32 chars for HS256)")
    JWT_EXPIRES_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRES_DAYS: int = 7
    TZ: str = "America/Sao_Paulo"
    CORS_ORIGINS: str = "http://localhost:5173,https://flow4-tech-sistema-de-gestao.vercel.app"
    ENV: str = Field(..., description="Deployment environment: dev, staging, prod, or test")
    SENTRY_DSN_BACKEND: str = ""
    APP_VERSION: str = "0.1.0"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    SUPERADMIN_TOKEN: str = Field("", description="Static bearer token for /admin/ routes")
    DATABASE_URL_PLATFORM: str = Field(..., description="Separate DB URL for platform engine (isolated role, no RLS)")
    DB_POOL_SIZE: int = Field(5, ge=1, description="Persistent connections kept per application pool")
    DB_MAX_OVERFLOW: int = Field(10, ge=0, description="Temporary connections allowed above pool size")
    DB_POOL_TIMEOUT: int = Field(30, ge=1, description="Seconds to wait for a database connection")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in {"dev", "staging", "prod", "test"}:
            raise ValueError("ENV must be one of: dev, staging, prod, test")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
