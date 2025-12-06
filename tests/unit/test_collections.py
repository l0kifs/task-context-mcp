"""Tests for collection management."""

import pytest
from task_context_mcp.database import (
    get_or_create_collection,
    get_task_catalog_collection,
    get_artifacts_collection,
    list_collections,
    delete_collection,
    TASK_CATALOG_COLLECTION,
    ARTIFACTS_COLLECTION,
)


def test_get_or_create_collection(test_settings):
    """Test creating a new collection."""
    collection = get_or_create_collection("test_collection")
    assert collection is not None
    assert collection.name == "test_collection"
    
    # Getting again should return existing collection
    collection2 = get_or_create_collection("test_collection")
    assert collection.name == collection2.name


def test_get_task_catalog_collection(test_settings):
    """Test getting task catalog collection."""
    collection = get_task_catalog_collection()
    assert collection is not None
    assert collection.name == TASK_CATALOG_COLLECTION


def test_get_artifacts_collection(test_settings):
    """Test getting artifacts collection."""
    collection = get_artifacts_collection()
    assert collection is not None
    assert collection.name == ARTIFACTS_COLLECTION


def test_list_collections(test_settings):
    """Test listing collections."""
    # Create some collections
    get_or_create_collection("test1")
    get_or_create_collection("test2")
    
    collections = list_collections()
    assert "test1" in collections
    assert "test2" in collections


def test_delete_collection(test_settings):
    """Test deleting a collection."""
    collection_name = "test_delete"
    get_or_create_collection(collection_name)
    
    # Verify it exists
    collections = list_collections()
    assert collection_name in collections
    
    # Delete it
    delete_collection(collection_name)
    
    # Verify it's gone
    collections = list_collections()
    assert collection_name not in collections
