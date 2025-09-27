"""Application configuration using Pydantic settings."""

import os

from .environments.base import BaseEnvironmentSettings
from .environments.development import DevelopmentSettings
from .environments.production import ProductionSettings
from .environments.testing import TestingSettings


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
