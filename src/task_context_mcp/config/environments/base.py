"""Base environment settings for all configurations."""

import os

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings:
    """Database configuration settings."""

    def __init__(self, url: SecretStr, echo: bool):
        """Initialize database settings."""
        self.url = url
        self.echo = echo


class BaseEnvironmentSettings(BaseSettings):
    """Base settings that all environments inherit from."""

    app_name: str = Field(
        default="Task Context MCP Server", description="Application name"
    )
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode flag")

    database_url: SecretStr = Field(
        default=SecretStr("sqlite+aiosqlite:///./tasks.db"),
        description="Database connection URL",
    )
    log_level: str = Field(default="INFO", description="Logging level")

    @property
    def database(self) -> "DatabaseSettings":
        """Get database settings as a nested object."""
        return DatabaseSettings(url=self.database_url, echo=self.debug)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: SecretStr) -> SecretStr:
        """Validate that database URL is properly configured."""
        url_value = v.get_secret_value()
        # Check if it's the default SQLite URL
        if url_value == "sqlite+aiosqlite:///./tasks.db":
            env = os.getenv("ENVIRONMENT", "development").lower()
            if env == "production":
                msg = "Database URL must be explicitly configured for production"
                raise ValueError(msg)
        return v

    model_config = SettingsConfigDict(
        env_prefix="TASK_CONTEXT_",
        env_file=[".env.local", ".env"],
        case_sensitive=False,
        env_nested_delimiter="__",
    )
