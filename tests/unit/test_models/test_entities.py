from datetime import UTC, datetime

from src.task_context_mcp.models.entities import Step, StepStatus, Task, TaskStatus


class TestTask:
    def test_create_task(self):
        """Test Task entity creation."""
        task_id = 1
        title = "Test Task"
        description = "Test Description"
        project_name = "test"
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        task = Task(
            id=task_id,
            title=title,
            description=description,
            project_name=project_name,
            status=TaskStatus.OPEN,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert task.id == task_id
        assert task.title == title
        assert task.description == description
        assert task.project_name == project_name
        assert task.status == TaskStatus.OPEN
        assert task.created_at == created_at
        assert task.updated_at == updated_at

    def test_step_creation(self):
        """Test Step entity creation."""
        step_id = 1
        task_id = 1
        name = "Step 1"
        description = "Step description"
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        step = Step(
            id=step_id,
            task_id=task_id,
            name=name,
            description=description,
            status=StepStatus.PENDING,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert step.id == step_id
        assert step.task_id == task_id
        assert step.name == name
        assert step.description == description
        assert step.status == StepStatus.PENDING
        assert step.created_at == created_at
        assert step.updated_at == updated_at

    def test_step_relationship(self):
        """Test Step relationship with Task."""
        created_at = datetime.now(UTC)
        task_id = 1
        task = Task(
            id=task_id,
            title="Test",
            description="Test",
            project_name="test",
            status=TaskStatus.OPEN,
            created_at=created_at,
            updated_at=created_at,
        )
        step = Step(
            id=None,
            task_id=task_id,
            name="Step 1",
            description="Done",
            status=StepStatus.PENDING,
            created_at=created_at,
            updated_at=created_at,
        )

        assert step.task_id == task.id
