import os

import pytest

from task_context_mcp.database.database import DatabaseManager
from task_context_mcp.database.models import (
    ArtifactStatus,
    ArtifactType,
    TaskContextStatus,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up in-memory database for tests."""
    # Override database URL to use in-memory SQLite
    os.environ["TASK_CONTEXT_MCP__DATABASE_URL"] = "sqlite:///:memory:"
    yield
    # Clean up after test
    if "TASK_CONTEXT_MCP__DATABASE_URL" in os.environ:
        del os.environ["TASK_CONTEXT_MCP__DATABASE_URL"]


@pytest.fixture
def db_manager():
    """Create a test database manager."""
    manager = DatabaseManager()
    manager.init_db()
    return manager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_init_db(self, db_manager):
        """Test database initialization."""
        db_manager.init_db()
        # Should not raise any exceptions
        assert db_manager.engine is not None

    def test_create_task_context(self, db_manager):
        """Test creating a new task context."""
        task_context = db_manager.create_task_context(
            summary="CV Analysis for Python Developer",
            description="Analyze applicant CVs for Python developer positions",
        )

        assert task_context is not None
        assert task_context.summary == "CV Analysis for Python Developer"
        assert (
            task_context.description
            == "Analyze applicant CVs for Python developer positions"
        )
        assert task_context.status == TaskContextStatus.ACTIVE.value

    def test_update_task_context(self, db_manager):
        """Test updating an existing task context."""
        # Create a task context first
        task_context = db_manager.create_task_context(
            summary="Original Task Context", description="Original description"
        )

        # Update the task context
        updated_task_context = db_manager.update_task_context(
            task_context_id=task_context.id,
            summary="Updated Task Context",
            description="Updated description",
        )

        assert updated_task_context is not None
        assert updated_task_context.summary == "Updated Task Context"
        assert updated_task_context.description == "Updated description"

    def test_update_task_context_not_found(self, db_manager):
        """Test updating a non-existent task context."""
        result = db_manager.update_task_context(
            task_context_id="non-existent-id", summary="Updated Task Context"
        )

        assert result is None

    def test_archive_task_context(self, db_manager):
        """Test archiving a task context."""
        # Create a task context first
        task_context = db_manager.create_task_context(
            summary="Task Context to Archive", description="Will be archived"
        )

        # Archive the task context
        archived_task_context = db_manager.archive_task_context(task_context.id)

        assert archived_task_context is not None
        assert archived_task_context.status == TaskContextStatus.ARCHIVED.value

    def test_archive_task_context_not_found(self, db_manager):
        """Test archiving a non-existent task context."""
        result = db_manager.archive_task_context("non-existent-id")

        assert result is None

    def test_get_active_task_contexts(self, db_manager):
        """Test getting all active task contexts."""
        # Create active task contexts
        active_tc1 = db_manager.create_task_context(
            summary="Active Task Context 1", description="First active task context"
        )
        active_tc2 = db_manager.create_task_context(
            summary="Active Task Context 2", description="Second active task context"
        )

        # Create an archived task context
        archived_tc = db_manager.create_task_context(
            summary="Archived Task Context", description="An archived task context"
        )
        db_manager.archive_task_context(archived_tc.id)

        # Get active task contexts
        active_task_contexts = db_manager.get_active_task_contexts()

        # Assert only active task contexts are returned
        assert len(active_task_contexts) == 2
        summaries = [tc.summary for tc in active_task_contexts]
        assert "Active Task Context 1" in summaries
        assert "Active Task Context 2" in summaries
        assert "Archived Task Context" not in summaries

    def test_create_artifact(self, db_manager):
        """Test creating a new artifact."""
        # Create a task context first
        task_context = db_manager.create_task_context(
            summary="Task Context for Artifact", description="Task context description"
        )

        # Create an artifact
        artifact = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice content",
            summary="Practice summary",
        )

        assert artifact is not None
        assert artifact.task_context_id == task_context.id
        assert artifact.artifact_type == ArtifactType.PRACTICE.value
        assert artifact.summary == "Practice summary"
        assert artifact.status == ArtifactStatus.ACTIVE.value

    def test_create_multiple_artifacts_same_type(self, db_manager):
        """Test creating multiple artifacts of the same type (now allowed)."""
        # Create a task context first
        task_context = db_manager.create_task_context(
            summary="Task Context for Multiple Artifacts",
            description="Task context description",
        )

        # Create first artifact
        artifact1 = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice 1 content",
            summary="First practice",
        )

        # Create second artifact of same type
        artifact2 = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice 2 content",
            summary="Second practice",
        )

        # Should be different artifacts
        assert artifact1.id != artifact2.id
        assert artifact1.task_context_id == task_context.id
        assert artifact2.task_context_id == task_context.id
        assert artifact1.content == "Practice 1 content"
        assert artifact2.content == "Practice 2 content"

        # Both should be retrievable
        artifacts = db_manager.get_artifacts_for_task_context(
            task_context.id, artifact_types=[ArtifactType.PRACTICE]
        )
        assert len(artifacts) == 2

    def test_update_artifact(self, db_manager):
        """Test updating an existing artifact."""
        # Create task context and artifact
        task_context = db_manager.create_task_context(
            summary="Task Context for Update", description="Task context description"
        )
        artifact = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Original content",
            summary="Original summary",
        )

        # Update the artifact
        updated_artifact = db_manager.update_artifact(
            artifact_id=artifact.id,
            content="Updated content",
            summary="Updated summary",
        )

        assert updated_artifact is not None
        assert updated_artifact.id == artifact.id
        assert updated_artifact.content == "Updated content"
        assert updated_artifact.summary == "Updated summary"

    def test_archive_artifact(self, db_manager):
        """Test archiving an artifact."""
        # Create task context and artifact
        task_context = db_manager.create_task_context(
            summary="Task Context for Archive", description="Task context description"
        )
        artifact = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Content",
            summary="Summary",
        )

        # Archive the artifact
        archived_artifact = db_manager.archive_artifact(artifact.id, "Test reason")

        assert archived_artifact is not None
        assert archived_artifact.status == ArtifactStatus.ARCHIVED.value
        assert archived_artifact.archivation_reason == "Test reason"
        assert archived_artifact.archived_at is not None

    def test_archive_artifact_not_found(self, db_manager):
        """Test archiving a non-existent artifact."""
        result = db_manager.archive_artifact("non-existent-id")

        assert result is None

    def test_get_artifacts_for_task_context_with_types(self, db_manager):
        """Test getting active artifacts with specific types."""
        # Create task context
        task_context = db_manager.create_task_context(
            summary="Task Context for Retrieval", description="Task context description"
        )

        # Create multiple artifacts of different types
        practice = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice content",
            summary="Practice summary",
        )
        rule = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.RULE,
            content="Rule content",
            summary="Rule summary",
        )
        prompt = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PROMPT,
            content="Prompt content",
            summary="Prompt summary",
        )
        result_artifact = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.RESULT,
            content="Pattern/learning from past work",
            summary="Learning summary",
        )

        # Get active artifacts of specific types
        results = db_manager.get_artifacts_for_task_context(
            task_context.id,
            artifact_types=[
                ArtifactType.PRACTICE,
                ArtifactType.RULE,
                ArtifactType.PROMPT,
            ],
        )

        # Should return practice, rule, prompt but not result
        assert len(results) == 3
        artifact_types = {artifact.artifact_type for artifact in results}
        assert artifact_types == {
            ArtifactType.PRACTICE.value,
            ArtifactType.RULE.value,
            ArtifactType.PROMPT.value,
        }

    def test_search_artifacts(self, db_manager):
        """Test searching artifacts using FTS."""
        # Create task context and artifact
        task_context = db_manager.create_task_context(
            summary="CV Analysis Task Context",
            description="Task context for CV analysis",
        )
        artifact = db_manager.create_artifact(
            task_context_id=task_context.id,
            artifact_type=ArtifactType.PRACTICE,
            content="This is some searchable content about Python programming",
            summary="Python practice",
        )

        # Search for content
        results = db_manager.search_artifacts("Python")
        assert len(results) == 1
        assert results[0][0] == artifact.id  # id
        assert "Python" in results[0][1]  # summary
