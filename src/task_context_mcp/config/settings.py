"""Application configuration using Pydantic settings."""

import os

from task_context_mcp.config.environments.base import BaseEnvironmentSettings
from task_context_mcp.config.environments.development import DevelopmentSettings
from task_context_mcp.config.environments.production import ProductionSettings
from task_context_mcp.config.environments.testing import TestingSettings


def get_settings() -> BaseEnvironmentSettings:
    """Get settings based on ENVIRONMENT variable."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    settings_map: dict[str, type[BaseEnvironmentSettings]] = {
        "development": DevelopmentSettings,
        "testing": TestingSettings,
        "production": ProductionSettings,
    }
    return settings_map.get(env, DevelopmentSettings)()


# Global settings instance
settings = get_settings()
