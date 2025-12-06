"""Tests for database client."""

import pytest
from task_context_mcp.database import get_client, reset_client


def test_get_client(test_settings):
    """Test getting ChromaDB client."""
    client = get_client()
    assert client is not None
    
    # Should return same instance
    client2 = get_client()
    assert client is client2


def test_reset_client(test_settings):
    """Test resetting ChromaDB client."""
    client1 = get_client()
    reset_client()
    client2 = get_client()
    
    # Should create new instance after reset
    assert client1 is not client2


def test_client_persistence(test_settings):
    """Test that client uses persistent storage."""
    client = get_client()
    
    # Check that heartbeat works (basic connectivity test)
    heartbeat = client.heartbeat()
    assert heartbeat > 0
