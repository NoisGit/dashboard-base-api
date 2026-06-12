"""Application configuration module for the Locentr API.

Defines the Settings class used to load and centralize environment
configuration (database, secrets, runtime environment, etc.).
"""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev_only_secret_key_change_me"  # nosec B105


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
    SMTP_FROM_EMAIL: str = Field(default="Locentr <admin@nois.dev>")
    EMAIL_DELIVERY_MODE: str = Field(default="log")
    EMAIL_QUEUE_SECRET: str = Field(default="")
    INVITATION_EXPIRE_HOURS: int = Field(default=72, ge=1, le=720)
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = Field(default=24, ge=1, le=168)

    # Logo URL setting
    LOGO_URL: str = Field(default="http://localhost:5173/logo.svg")

    # Front URL Setting
    FRONT_URL_BASE: str = Field(default="http://localhost:5173")

    # CORS settings
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    # Storage settings
    storage_public_base_url: str | None = Field(
        default=None,
        alias="STORAGE_PUBLIC_BASE_URL",
    )
    storage_bucket_name: str = Field(default="locentr", alias="STORAGE_BUCKET_NAME")
    backend_public_base_url: str = Field(
        default="http://localhost:8000",
        alias="BACKEND_PUBLIC_BASE_URL",
    )
    private_storage_root: str = Field(
        default="private_storage",
        alias="PRIVATE_STORAGE_ROOT",
    )
    storage_signed_url_expire_seconds: int = Field(
        default=300,
        alias="STORAGE_SIGNED_URL_EXPIRE_SECONDS",
        ge=60,
        le=3600,
    )

    # SaaS billing settings
    trial_days: int = Field(default=14, alias="TRIAL_DAYS", ge=1, le=90)
    trial_plan_code: str = Field(default="growth", alias="TRIAL_PLAN_CODE")
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    STRIPE_PRICE_STARTER: str = Field(default="")
    STRIPE_PRICE_GROWTH: str = Field(default="")
    STRIPE_PRICE_SCALE: str = Field(default="")
    BILLING_RECONCILIATION_SECRET: str = Field(default="")

    # Supabase compatibility settings
    SUPABASE_URL: str | None = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: str | None = Field(default=None)
    SUPABASE_STORAGE_BUCKET: str | None = Field(default=None)

    # Auth settings
    secret_key: str = Field(
        default=DEV_SECRET_KEY,
        alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    max_request_body_bytes: int = Field(
        default=10 * 1024 * 1024,
        alias="MAX_REQUEST_BODY_BYTES",
    )
    auth_rate_limit_requests: int = Field(
        default=10,
        alias="AUTH_RATE_LIMIT_REQUESTS",
    )
    auth_rate_limit_window_seconds: int = Field(
        default=60,
        alias="AUTH_RATE_LIMIT_WINDOW_SECONDS",
    )

    # pydantic-settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore extra vars in .env instead of failing
    )

    @model_validator(mode="after")
    def validate_secure_defaults(self):
        """Prevent unsafe defaults in deployed environments."""
        normalized_env = self.env.lower().strip()
        is_production = normalized_env in {"prod", "production"}

        if not self.secret_key.strip():
            if is_production:
                raise ValueError("SECRET_KEY is required in production")
            self.secret_key = DEV_SECRET_KEY

        if is_production and self.secret_key == DEV_SECRET_KEY:
            raise ValueError("SECRET_KEY must be changed in production")

        if is_production and len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")

        if is_production and not self.database_url:
            raise ValueError("DATABASE_URL is required in production")

        if is_production and (not self.cors_origins or "*" in self.cors_origins):
            raise ValueError(
                "BACKEND_CORS_ORIGINS must list explicit origins in production"
            )

        return self

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

    @property
    def storage_bucket(self) -> str:
        """Storage bucket name."""
        return (self.SUPABASE_STORAGE_BUCKET or self.storage_bucket_name).strip("/")

    @property
    def storage_base_url(self) -> str:
        """Public storage base URL."""
        if self.storage_public_base_url:
            return self.storage_public_base_url.rstrip("/")

        supabase_url = (self.SUPABASE_URL or "http://localhost:54321").rstrip("/")
        return f"{supabase_url}/storage/v1/object/public/{self.storage_bucket}"


settings = Settings()
