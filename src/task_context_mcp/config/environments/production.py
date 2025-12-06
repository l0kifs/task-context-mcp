"""Production environment settings."""

from pydantic import Field, SecretStr

from task_context_mcp.config.environments.base import BaseEnvironmentSettings


class ProductionSettings(BaseEnvironmentSettings):
    """Settings for production environment."""

    debug: bool = False
    database_url: SecretStr = Field(
        description="Database connection URL",
    )
    log_level: str = "WARNING"
