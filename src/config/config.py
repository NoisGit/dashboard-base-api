"""Application configuration module for the Sentinel Enterprise API.

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

    # Granular DB configuration
    db_host: str | None = Field(default=None, alias="DB_HOST")
    db_user: str | None = Field(default=None, alias="DB_USER")
    db_pass: str | None = Field(default=None, alias="DB_PASS")
    db_name: str | None = Field(default=None, alias="DB_NAME")

    # Legacy / compatibility: full DATABASE_URL
    database_url_env: str | None = Field(default=None, alias="DATABASE_URL")

    # SMTP settings
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str

    # Logo URL setting
    LOGO_URL: str

    # Front URL Setting
    FRONT_URL_BASE: str

    # Azure Storage settings
    AZURE_STORAGE_ACCOUNT_NAME: str
    AZURE_STORAGE_CONNECTION_STRING: str

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
    def database_url(self) -> str:
        """
        Final database URL.

        Priority:
        1) If DATABASE_URL exists, use it as-is (legacy mode).
        2) Otherwise, build the URL from DB_HOST, DB_USER, DB_PASS, DB_NAME.
        """
        if self.database_url_env:
            return self.database_url_env

        if not all([self.db_host, self.db_user, self.db_pass, self.db_name]):
            raise ValueError(
                "Database configuration is incomplete. "
                "Set DATABASE_URL or DB_HOST, DB_USER, DB_PASS, DB_NAME.",
            )

        # Adjust dialect later if the team switches to PostgreSQL or another engine
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}/{self.db_name}"
        )


settings = Settings()
