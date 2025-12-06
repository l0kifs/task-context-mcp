"""Tests for task catalog repository."""

import pytest
from task_context_mcp.repositories import TaskCatalogRepository


def test_register_task_type(test_settings):
    """Test registering a new task type."""
    repo = TaskCatalogRepository()
    
    task_type = repo.register_task_type(
        task_type="test_task",
        description="A test task type"
    )
    
    assert task_type.task_type == "test_task"
    assert task_type.description == "A test task type"
    assert task_type.created_at is not None
    assert task_type.updated_at is not None


def test_get_task_type(test_settings):
    """Test retrieving a task type."""
    repo = TaskCatalogRepository()
    
    # Register first
    repo.register_task_type(
        task_type="test_task",
        description="A test task type"
    )
    
    # Retrieve
    task_type = repo.get_task_type("test_task")
    assert task_type is not None
    assert task_type.task_type == "test_task"
    assert task_type.description == "A test task type"


def test_get_nonexistent_task_type(test_settings):
    """Test retrieving a non-existent task type."""
    repo = TaskCatalogRepository()
    
    task_type = repo.get_task_type("nonexistent")
    assert task_type is None


def test_list_task_types(test_settings):
    """Test listing all task types."""
    repo = TaskCatalogRepository()
    
    # Register multiple
    repo.register_task_type("task1", "Description 1")
    repo.register_task_type("task2", "Description 2")
    repo.register_task_type("task3", "Description 3")
    
    # List
    task_types = repo.list_task_types()
    assert len(task_types) == 3
    
    task_type_names = [t.task_type for t in task_types]
    assert "task1" in task_type_names
    assert "task2" in task_type_names
    assert "task3" in task_type_names


def test_update_task_type(test_settings):
    """Test updating a task type."""
    repo = TaskCatalogRepository()
    
    # Register
    original = repo.register_task_type("test_task", "Original description")
    
    # Update
    updated = repo.update_task_type("test_task", "Updated description")
    
    assert updated.task_type == "test_task"
    assert updated.description == "Updated description"
    assert updated.created_at == original.created_at
    assert updated.updated_at > original.updated_at


def test_update_nonexistent_task_type(test_settings):
    """Test updating a non-existent task type."""
    repo = TaskCatalogRepository()
    
    with pytest.raises(ValueError, match="not found"):
        repo.update_task_type("nonexistent", "New description")
