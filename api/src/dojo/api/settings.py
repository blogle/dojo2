from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_base_url: str = Field(default="http://localhost:5173", alias="APP_BASE_URL")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    frontend_base_url: str = Field(default="http://localhost:5173", alias="FRONTEND_BASE_URL")
    duckdb_path: str = Field(default=".local/dojo.duckdb", alias="DUCKDB_PATH")
    google_oauth_client_id: str = Field(default="", alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str = Field(default="", alias="GOOGLE_OAUTH_CLIENT_SECRET")
    google_oauth_redirect_uri: str = Field(
        default="http://localhost:8000/api/onboarding/google/callback",
        alias="GOOGLE_OAUTH_REDIRECT_URI",
    )
    google_oauth_scopes: str = Field(
        default="https://www.googleapis.com/auth/spreadsheets.readonly",
        alias="GOOGLE_OAUTH_SCOPES",
    )
    session_secret: str = Field(default="dev-only-change-me", alias="SESSION_SECRET")
    log_level: str = Field(default="debug", alias="LOG_LEVEL")
    cors_allowed_origins: str = Field(default="http://localhost:5173", alias="CORS_ALLOWED_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
