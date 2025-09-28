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

    async def test_list_tasks_with_project_filter_integration(
        self, integration_task_service
    ):
        """Test project filtering with real database through full service stack."""
        # Create tasks in different projects
        project_a_tasks = []
        project_b_tasks = []

        # Create multiple tasks in project-a
        for i in range(3):
            task_id = await integration_task_service.create_task(
                f"Project A Task {i}",
                f"Description for project A task {i}",
                project_name="project-a",
            )
            project_a_tasks.append(task_id)

        # Create multiple tasks in project-b
        for i in range(2):
            task_id = await integration_task_service.create_task(
                f"Project B Task {i}",
                f"Description for project B task {i}",
                project_name="project-b",
            )
            project_b_tasks.append(task_id)

        # Test filtering by project-a
        result = await integration_task_service.list_tasks(project_filter="project-a")

        assert result is not None
        assert len(result.tasks) == 3

        # Verify all returned tasks are from project-a
        for task in result.tasks:
            assert task["project_name"] == "project-a"
            assert task["id"] in project_a_tasks

        # Test filtering by project-b
        result = await integration_task_service.list_tasks(project_filter="project-b")

        assert result is not None
        assert len(result.tasks) == 2

        # Verify all returned tasks are from project-b
        for task in result.tasks:
            assert task["project_name"] == "project-b"
            assert task["id"] in project_b_tasks

        # Test with non-existent project
        result = await integration_task_service.list_tasks(
            project_filter="non-existent-project"
        )

        assert result is not None
        assert len(result.tasks) == 0

        # Test combined filtering (project + status)
        # First update one project-a task to closed
        await integration_task_service.update_task_status(
            project_a_tasks[0], TaskStatus.CLOSED
        )

        # Filter by project-a and open status
        result = await integration_task_service.list_tasks(
            project_filter="project-a", status_filter=TaskStatus.OPEN
        )

        assert result is not None
        assert len(result.tasks) == 2  # 2 open tasks in project-a

        for task in result.tasks:
            assert task["project_name"] == "project-a"
            assert task["status"] == TaskStatus.OPEN
            assert task["id"] in project_a_tasks[1:]  # Exclude the closed one

        # Filter by project-a and closed status
        result = await integration_task_service.list_tasks(
            project_filter="project-a", status_filter=TaskStatus.CLOSED
        )

        assert result is not None
        assert len(result.tasks) == 1
        assert result.tasks[0]["project_name"] == "project-a"
        assert result.tasks[0]["status"] == TaskStatus.CLOSED
        assert result.tasks[0]["id"] == project_a_tasks[0]
