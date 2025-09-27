"""Development environment settings."""

from pydantic import Field, SecretStr

from .base import BaseEnvironmentSettings


class DevelopmentSettings(BaseEnvironmentSettings):
    """Settings for development environment."""

    debug: bool = True
    database_url: SecretStr = Field(
        default=SecretStr("sqlite+aiosqlite:///./src/task_context_mcp/data/db/dev.db")
    )
    log_level: str = "DEBUG"
