"""Testing environment settings."""

from pydantic import Field, SecretStr

from task_context_mcp.config.environments.base import BaseEnvironmentSettings


class TestingSettings(BaseEnvironmentSettings):
    """Settings for testing environment."""

    debug: bool = True
    database_url: SecretStr = Field(default=SecretStr("sqlite+aiosqlite:///:memory:"))
    log_level: str = "DEBUG"
