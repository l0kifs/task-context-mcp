"""Tests for artifact repository."""

import pytest
from task_context_mcp.repositories import ArtifactRepository
from task_context_mcp.database import ArtifactType, ArtifactStatus


def test_add_artifact(test_settings, mock_sentence_transformer):
    """Test adding a new artifact."""
    repo = ArtifactRepository()
    
    artifact = repo.add_artifact(
        task_type="test_task",
        artifact_type=ArtifactType.PRACTICE,
        content="This is a test practice",
        metadata={"priority": "high"}
    )
    
    assert artifact.artifact_id is not None
    assert artifact.task_type == "test_task"
    assert artifact.artifact_type == ArtifactType.PRACTICE
    assert artifact.version == 1
    assert artifact.content == "This is a test practice"
    assert artifact.metadata["priority"] == "high"
    assert artifact.status == ArtifactStatus.ACTIVE


def test_get_artifact(test_settings, mock_sentence_transformer):
    """Test retrieving an artifact."""
    repo = ArtifactRepository()
    
    # Add artifact
    original = repo.add_artifact(
        task_type="test_task",
        artifact_type=ArtifactType.RULE,
        content="Test rule content"
    )
    
    # Retrieve
    retrieved = repo.get_artifact(original.artifact_id)
    assert retrieved is not None
    assert retrieved.artifact_id == original.artifact_id
    assert retrieved.content == "Test rule content"
    assert retrieved.version == 1


def test_get_artifact_specific_version(test_settings, mock_sentence_transformer):
    """Test retrieving a specific version of an artifact."""
    repo = ArtifactRepository()
    
    # Add artifact
    original = repo.add_artifact(
        task_type="test_task",
        artifact_type=ArtifactType.PROMPT,
        content="Version 1"
    )
    
    # Update to create version 2
    repo.update_artifact(original.artifact_id, "Version 2")
    
    # Retrieve version 1
    v1 = repo.get_artifact(original.artifact_id, version=1)
    assert v1 is not None
    assert v1.version == 1
    assert v1.content == "Version 1"
    
    # Retrieve latest (should be version 2)
    latest = repo.get_artifact(original.artifact_id)
    assert latest is not None
    assert latest.version == 2
    assert latest.content == "Version 2"


def test_update_artifact(test_settings, mock_sentence_transformer):
    """Test updating an artifact creates a new version."""
    repo = ArtifactRepository()
    
    # Add artifact
    original = repo.add_artifact(
        task_type="test_task",
        artifact_type=ArtifactType.RESULT,
        content="Original content"
    )
    
    # Update
    updated = repo.update_artifact(
        original.artifact_id,
        "Updated content",
        metadata={"status": "reviewed"}
    )
    
    assert updated.artifact_id == original.artifact_id
    assert updated.version == 2
    assert updated.content == "Updated content"
    assert updated.metadata["status"] == "reviewed"
    
    # Verify old version still exists
    old_version = repo.get_artifact(original.artifact_id, version=1)
    assert old_version is not None
    assert old_version.content == "Original content"


def test_delete_artifact(test_settings, mock_sentence_transformer):
    """Test soft delete of an artifact."""
    repo = ArtifactRepository()
    
    # Add artifact
    artifact = repo.add_artifact(
        task_type="test_task",
        artifact_type=ArtifactType.PRACTICE,
        content="To be deleted"
    )
    
    # Delete
    deleted = repo.delete_artifact(
        artifact.artifact_id,
        reason="No longer needed",
        replacement_id="new_artifact_123"
    )
    
    assert deleted.status == ArtifactStatus.ARCHIVED
    assert deleted.deprecated_reason == "No longer needed"
    assert deleted.replacement_id == "new_artifact_123"
    assert deleted.deprecated_at is not None


def test_list_artifacts(test_settings, mock_sentence_transformer):
    """Test listing artifacts with filters."""
    repo = ArtifactRepository()
    
    # Add multiple artifacts
    repo.add_artifact("task1", ArtifactType.PRACTICE, "Practice 1")
    repo.add_artifact("task1", ArtifactType.RULE, "Rule 1")
    repo.add_artifact("task2", ArtifactType.PRACTICE, "Practice 2")
    
    # List all active
    all_artifacts = repo.list_artifacts()
    assert len(all_artifacts) == 3
    
    # Filter by task_type
    task1_artifacts = repo.list_artifacts(task_type="task1")
    assert len(task1_artifacts) == 2
    
    # Filter by artifact_type
    practices = repo.list_artifacts(artifact_type=ArtifactType.PRACTICE)
    assert len(practices) == 2


def test_list_artifacts_excludes_archived(test_settings, mock_sentence_transformer):
    """Test that listing excludes archived artifacts by default."""
    repo = ArtifactRepository()
    
    # Add artifacts
    artifact1 = repo.add_artifact("task1", ArtifactType.PRACTICE, "Active")
    artifact2 = repo.add_artifact("task1", ArtifactType.RULE, "To archive")
    
    # Archive one
    repo.delete_artifact(artifact2.artifact_id)
    
    # List active only
    active_artifacts = repo.list_artifacts()
    assert len(active_artifacts) == 1
    assert active_artifacts[0].artifact_id == artifact1.artifact_id
    
    # List archived
    archived_artifacts = repo.list_artifacts(status=ArtifactStatus.ARCHIVED)
    assert len(archived_artifacts) == 1
    assert archived_artifacts[0].artifact_id == artifact2.artifact_id


def test_update_nonexistent_artifact(test_settings, mock_sentence_transformer):
    """Test updating a non-existent artifact."""
    repo = ArtifactRepository()
    
    with pytest.raises(ValueError, match="not found"):
        repo.update_artifact("nonexistent_id", "New content")


def test_delete_nonexistent_artifact(test_settings, mock_sentence_transformer):
    """Test deleting a non-existent artifact."""
    repo = ArtifactRepository()
    
    with pytest.raises(ValueError, match="not found"):
        repo.delete_artifact("nonexistent_id")
