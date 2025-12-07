import os

import pytest

from task_context_mcp.database.database import DatabaseManager
from task_context_mcp.database.models import (
    ArtifactStatus,
    ArtifactType,
    TaskStatus,
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

    def test_create_task(self, db_manager):
        """Test creating a new task."""
        task = db_manager.create_task(summary="Test Task", description="A test task")

        assert task is not None
        assert task.summary == "Test Task"
        assert task.description == "A test task"
        assert task.status == TaskStatus.ACTIVE.value

    def test_update_task(self, db_manager):
        """Test updating an existing task."""
        # Create a task first
        task = db_manager.create_task(
            summary="Original Task", description="Original description"
        )

        # Update the task
        updated_task = db_manager.update_task(
            task_id=task.id, summary="Updated Task", description="Updated description"
        )

        assert updated_task is not None
        assert updated_task.summary == "Updated Task"
        assert updated_task.description == "Updated description"

    def test_update_task_not_found(self, db_manager):
        """Test updating a non-existent task."""
        result = db_manager.update_task(
            task_id="non-existent-id", summary="Updated Task"
        )

        assert result is None

    def test_archive_task(self, db_manager):
        """Test archiving a task."""
        # Create a task first
        task = db_manager.create_task(
            summary="Task to Archive", description="Will be archived"
        )

        # Archive the task
        archived_task = db_manager.archive_task(task.id)

        assert archived_task is not None
        assert archived_task.status == TaskStatus.ARCHIVED.value

    def test_archive_task_not_found(self, db_manager):
        """Test archiving a non-existent task."""
        result = db_manager.archive_task("non-existent-id")

        assert result is None

    def test_get_active_tasks(self, db_manager):
        """Test getting all active tasks."""
        # Create active tasks
        active_task1 = db_manager.create_task(
            summary="Active Task 1", description="First active task"
        )
        active_task2 = db_manager.create_task(
            summary="Active Task 2", description="Second active task"
        )

        # Create an archived task
        archived_task = db_manager.create_task(
            summary="Archived Task", description="An archived task"
        )
        db_manager.archive_task(archived_task.id)

        # Get active tasks
        active_tasks = db_manager.get_active_tasks()

        # Assert only active tasks are returned
        assert len(active_tasks) == 2
        summaries = [task.summary for task in active_tasks]
        assert "Active Task 1" in summaries
        assert "Active Task 2" in summaries
        assert "Archived Task" not in summaries

    def test_create_artifact(self, db_manager):
        """Test creating a new artifact."""
        # Create a task first
        task = db_manager.create_task(
            summary="Task for Artifact", description="Task description"
        )

        # Create an artifact
        artifact = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice content",
            summary="Practice summary",
        )

        assert artifact is not None
        assert artifact.task_id == task.id
        assert artifact.artifact_type == ArtifactType.PRACTICE.value
        assert artifact.summary == "Practice summary"
        assert artifact.status == ArtifactStatus.ACTIVE.value

    def test_create_artifact_multiple_versions(self, db_manager):
        """Test updating an existing artifact."""
        # Create a task first
        task = db_manager.create_task(
            summary="Task for Versions", description="Task description"
        )

        # Create first artifact
        artifact1 = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Version 1 content",
            summary="Practice summary",
        )

        # Update the artifact
        artifact2 = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Version 2 content",
            summary="Updated practice summary",
        )

        assert artifact1.id == artifact2.id  # Same artifact
        assert artifact1.task_id == task.id
        assert artifact2.task_id == task.id
        assert artifact2.content == "Version 2 content"
        assert artifact2.summary == "Updated practice summary"

    def test_archive_artifact(self, db_manager):
        """Test archiving an artifact."""
        # Create task and artifact
        task = db_manager.create_task(
            summary="Task for Archive", description="Task description"
        )
        artifact = db_manager.create_artifact(
            task_id=task.id,
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

    def test_get_artifacts_for_task_with_types(self, db_manager):
        """Test getting active artifacts with specific types."""
        # Create task
        task = db_manager.create_task(
            summary="Task for Retrieval", description="Task description"
        )

        # Create multiple artifacts
        practice = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PRACTICE,
            content="Practice content",
            summary="Practice summary",
        )
        rule = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.RULE,
            content="Rule content",
            summary="Rule summary",
        )
        prompt = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PROMPT,
            content="Prompt content",
            summary="Prompt summary",
        )
        result_artifact = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.RESULT,
            content="Result content",
            summary="Result summary",
        )

        # Get active artifacts of specific types
        results = db_manager.get_artifacts_for_task(
            task.id,
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
        # Create task and artifact
        task = db_manager.create_task(
            summary="Search Test Task", description="Task for search testing"
        )
        artifact = db_manager.create_artifact(
            task_id=task.id,
            artifact_type=ArtifactType.PRACTICE,
            content="This is some searchable content about Python programming",
            summary="Python practice",
        )

        # Search for content
        results = db_manager.search_artifacts("Python")
        assert len(results) == 1
        assert results[0][0] == artifact.id  # id
        assert "Python" in results[0][1]  # summary
