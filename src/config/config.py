"""Application configuration module for the Coredeck API.

Defines the Settings class used to load and centralize environment
configuration (database, secrets, runtime environment, etc.).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralizes project configuration.

    - Reads variables from .env (or the system environment)
    - Exposes typed properties (env, debug, database_url, etc.)
    """

    # Runtime environment
    env: str = Field(default="dev", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # Database settings
    database_url_env: str | None = Field(default=None, alias="DATABASE_URL")

    # SMTP settings
    SMTP_SERVER: str = Field(default="smtp.example.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="admin@nois.dev")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="Coredeck <admin@nois.dev>")

    # Logo URL setting
    LOGO_URL: str = Field(default="http://localhost:5173/logo.svg")

    # Front URL Setting
    FRONT_URL_BASE: str = Field(default="http://localhost:5173")

    # CORS settings
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    # Supabase Storage settings
    SUPABASE_URL: str | None = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: str | None = Field(default=None)
    SUPABASE_STORAGE_BUCKET: str = Field(default="coredeck")

    # Secret key for JWT or other security purposes
    secret_key: str = Field(
        default="change_this_secret_key",
        alias="SECRET_KEY",
    )

    # pydantic-settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore extra vars in .env instead of failing
    )

    @property
    def database_url(self) -> str | None:
        """database URL."""
        return self.database_url_env

    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins parsed from a comma-separated environment value."""
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
