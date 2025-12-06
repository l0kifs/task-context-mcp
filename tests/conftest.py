"""Pytest configuration and fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

from task_context_mcp.database import reset_client
from task_context_mcp.services import reset_model


@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary database directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Reset database client after each test."""
    yield
    try:
        reset_client()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def test_settings(temp_db_path, monkeypatch):
    """Override settings for testing."""
    monkeypatch.setenv("TASK_CONTEXT_MCP__DB_PATH", temp_db_path)
    monkeypatch.setenv("TASK_CONTEXT_MCP__LOGGING_LEVEL", "ERROR")
    # Disable ChromaDB telemetry to avoid network calls
    monkeypatch.setenv("CHROMA_TELEMETRY", "false")
    from task_context_mcp.config.settings import Settings
    return Settings()


@pytest.fixture(scope="function")
def mock_sentence_transformer(monkeypatch):
    """Mock SentenceTransformer for tests (no internet access to HuggingFace)."""
    mock_model = MagicMock()
    
    def mock_encode(texts, convert_to_numpy=False, show_progress_bar=False):
        # Generate fake embeddings with dimension 384
        if isinstance(texts, str):
            texts = [texts]
        embeddings = np.random.rand(len(texts), 384)
        return embeddings if convert_to_numpy else embeddings.tolist()
    
    mock_model.encode = mock_encode
    
    def mock_st_init(*args, **kwargs):
        return mock_model
    
    monkeypatch.setattr("task_context_mcp.services.embeddings.SentenceTransformer", mock_st_init)
    return mock_model
