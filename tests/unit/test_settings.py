"""Tests for settings."""

import os
import pytest
from task_context_mcp.config.settings import Settings, get_settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()
    
    assert settings.app_name == "task-context-mcp"
    assert settings.app_version == "0.1.0"
    assert settings.logging_level == "INFO"
    assert settings.db_path == "./data/chromadb"
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dimension == 384


def test_settings_from_env(monkeypatch):
    """Test loading settings from environment variables."""
    monkeypatch.setenv("TASK_CONTEXT_MCP__APP_NAME", "test-app")
    monkeypatch.setenv("TASK_CONTEXT_MCP__LOGGING_LEVEL", "DEBUG")
    monkeypatch.setenv("TASK_CONTEXT_MCP__DB_PATH", "/tmp/test_db")
    monkeypatch.setenv("TASK_CONTEXT_MCP__EMBEDDING_MODEL", "test-model")
    monkeypatch.setenv("TASK_CONTEXT_MCP__EMBEDDING_DIMENSION", "512")
    
    settings = Settings()
    
    assert settings.app_name == "test-app"
    assert settings.logging_level == "DEBUG"
    assert settings.db_path == "/tmp/test_db"
    assert settings.embedding_model == "test-model"
    assert settings.embedding_dimension == 512


def test_get_settings():
    """Test get_settings function."""
    settings = get_settings()
    assert isinstance(settings, Settings)
