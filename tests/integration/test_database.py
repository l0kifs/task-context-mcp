import pytest

from src.task_context_mcp.models.entities import TaskStatus


@pytest.mark.asyncio
class TestTaskRepositoryIntegration:
    """Integration tests for TaskRepository with real database."""

    async def test_save_and_get_task(self, integration_task_service):
        """Test saving and retrieving a task."""
        title = "Integration Test Task"
        description = "Testing with real DB"

        # Create task
        task_id = await integration_task_service.create_task(
            title, description, project_name="test"
        )
        assert isinstance(task_id, int)

        # Retrieve task
        retrieved = await integration_task_service.get_task(task_id)
        assert retrieved is not None
        assert retrieved.id == task_id
        assert retrieved.title == title
        assert retrieved.description == description

    async def test_create_and_get_steps(self, integration_task_service):
        """Test creating and retrieving task steps."""
        # First create a task
        task_id = await integration_task_service.create_task(
            "Test Task", "Test Description", project_name="test"
        )

        steps_data = [
            {"step_number": 1, "description": "First step"},
            {"step_number": 2, "description": "Second step"},
        ]

        # Create steps
        result = await integration_task_service.create_task_steps(task_id, steps_data)
        assert result is True

        # Get context
        context = await integration_task_service.get_task_context(task_id)
        assert context is not None
        assert context.task_id == task_id
        assert context.total_steps == 2
        assert "First step" in context.context_summary
        assert "Second step" in context.context_summary

    async def test_list_tasks(self, integration_task_service):
        """Test listing tasks."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await integration_task_service.create_task(
                f"Task {i}", f"Desc {i}", project_name="test"
            )
            task_ids.append(task_id)

        result = await integration_task_service.list_tasks()
        tasks = result.tasks
        assert len(tasks) >= 3

        # Check that our tasks are in the list
        task_ids_in_list = {task["id"] for task in tasks}
        for task_id in task_ids:
            assert task_id in task_ids_in_list

    async def test_update_task_status(self, integration_task_service):
        """Test updating task status."""
        task_id = await integration_task_service.create_task(
            "Test", "Test", project_name="test"
        )

        # Update status
        result = await integration_task_service.update_task_status(
            task_id, TaskStatus.CLOSED
        )
        assert result is True

        # Verify status
        task = await integration_task_service.get_task(task_id)
        assert task.status == TaskStatus.CLOSED

    async def test_delete_task(self, integration_task_service):
        """Test deleting a task."""
        task_id = await integration_task_service.create_task(
            "Test", "Test", project_name="test"
        )

        # Delete task
        await integration_task_service.delete_task(task_id)

        # Verify deletion
        task = await integration_task_service.get_task(task_id)
        assert task is None
