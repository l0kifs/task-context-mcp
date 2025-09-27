from datetime import UTC, datetime

from src.task_context_mcp.models.entities import Task, TaskStatus, TaskSummary


class TestTask:
    def test_create_task(self):
        """Test Task entity creation."""
        task_id = 1
        title = "Test Task"
        description = "Test Description"
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.OPEN,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert task.id == task_id
        assert task.title == title
        assert task.description == description
        assert task.status == TaskStatus.OPEN
        assert task.created_at == created_at
        assert task.updated_at == updated_at

    def test_task_summary_creation(self):
        """Test TaskSummary entity creation."""
        task_id = 1
        summary_text = "Task summary"
        step_number = 1
        created_at = datetime.now(UTC)

        summary = TaskSummary(
            id=None,
            task_id=task_id,
            step_number=step_number,
            summary=summary_text,
            created_at=created_at,
        )

        assert summary.task_id == task_id
        assert summary.summary == summary_text
        assert summary.step_number == step_number
        assert summary.created_at == created_at

    def test_task_summary_relationship(self):
        """Test TaskSummary relationship with Task."""
        task_id = 1
        created_at = datetime.now(UTC)
        task = Task(
            id=task_id,
            title="Test",
            description="Test",
            status=TaskStatus.OPEN,
            created_at=created_at,
            updated_at=created_at,
        )
        summary = TaskSummary(
            id=None,
            task_id=task_id,
            step_number=1,
            summary="Done",
            created_at=created_at,
        )

        assert summary.task_id == task.id
