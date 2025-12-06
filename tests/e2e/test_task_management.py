"""End-to-end tests for critical application scenarios."""

import pytest

from task_context_mcp.business.services import TaskService
from task_context_mcp.integrations.database.repositories import (
    StepRepositoryImpl,
    TaskRepositoryImpl,
)
from task_context_mcp.models.entities import TaskStatus
from task_context_mcp.models.value_objects import TaskListParams

# Test constants
TASK_COUNT = 5
COMPLETED_THRESHOLD = 3
OPEN_TASK_COUNT = 3
COMPLETED_TASK_COUNT = 2
PAGE_SIZE = 2
MULTI_STEP_COUNT = 5


class TestTaskManagementE2E:
    """E2E tests for task management workflow."""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self, db_manager):
        """
        Test complete task lifecycle: create, update, add steps, complete.

        This E2E test covers the critical user journey of managing a task
        from creation to completion.
        """
        # Setup
        await db_manager.initialize()
        task_repo = TaskRepositoryImpl(db_manager.get_session())
        step_repo = StepRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, step_repo)

        # Step 1: Create a task
        task_id = await service.create_task(
            title="E2E Test Task",
            description="Testing complete task lifecycle",
            project_name="test",
        )
        assert task_id is not None

        # Step 2: Get the task and verify creation
        task = await service.get_task(task_id)
        assert task is not None
        assert task.title == "E2E Test Task"
        assert task.status == TaskStatus.OPEN

        # Step 3: Add steps
        steps_data = [{"step_number": 1, "description": "Initial analysis completed"}]
        steps_added = await service.create_task_steps(task_id, steps_data)
        assert steps_added is True

        # Step 4: Get task context and verify steps
        context = await service.get_task_context(task_id)
        assert context is not None
        assert context.task_id == task_id
        assert context.total_steps == 1
        assert "Initial analysis completed" in context.context_summary

        # Step 5: Update task status to closed
        status_updated = await service.update_task_status(task_id, "closed")
        assert status_updated is True

        # Step 6: Verify final state
        updated_task = await service.get_task(task_id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.CLOSED

        # Cleanup
        deleted = await service.delete_task(task_id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_task_listing_and_filtering(self, db_manager):
        """
        Test task listing with filtering and pagination.

        This E2E test covers task discovery and filtering capabilities.
        """
        # Setup
        await db_manager.initialize()
        task_repo = TaskRepositoryImpl(db_manager.get_session())
        step_repo = StepRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, step_repo)

        # Create test tasks
        task_ids = []
        for i in range(TASK_COUNT):
            task_id = await service.create_task(
                title=f"Test Task {i}",
                description=f"Description {i}",
                project_name="test",
            )
            task_ids.append(task_id)

            # Mark some as closed
            if i >= COMPLETED_THRESHOLD:
                await service.update_task_status(task_id, "closed")

        # Test listing all tasks
        params = TaskListParams()
        all_tasks = await service.list_tasks(params)
        assert len(all_tasks.tasks) == TASK_COUNT

        # Test filtering by status
        params = TaskListParams(status_filter="open")
        open_tasks = await service.list_tasks(params)
        assert len(open_tasks.tasks) == OPEN_TASK_COUNT

        params = TaskListParams(status_filter="closed")
        closed_tasks = await service.list_tasks(params)
        assert len(closed_tasks.tasks) == COMPLETED_TASK_COUNT

        # Test pagination
        params = TaskListParams(page=1, page_size=PAGE_SIZE)
        paginated = await service.list_tasks(params)
        assert len(paginated.tasks) == PAGE_SIZE
        assert paginated.pagination.total_count == TASK_COUNT

        # Cleanup
        for task_id in task_ids:
            await service.delete_task(task_id)

    @pytest.mark.asyncio
    async def test_task_with_multiple_steps(self, db_manager):
        """
        Test task with multiple steps.

        This E2E test covers the scenario of tracking task progress
        through multiple steps.
        """
        # Setup
        await db_manager.initialize()
        task_repo = TaskRepositoryImpl(db_manager.get_session())
        step_repo = StepRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, step_repo)

        # Create task
        task_id = await service.create_task(
            title="Multi-step Task",
            description="Task with multiple progress steps",
            project_name="test",
        )

        # Add multiple steps
        steps_data = [
            {"step_number": 1, "description": "Step 1: Initial planning"},
            {"step_number": 2, "description": "Step 2: Implementation started"},
            {"step_number": 3, "description": "Step 3: Core functionality complete"},
            {"step_number": 4, "description": "Step 4: Testing and validation"},
            {"step_number": 5, "description": "Step 5: Final review and completion"},
        ]

        added = await service.create_task_steps(task_id, steps_data)
        assert added is True

        # Verify context includes all steps
        context = await service.get_task_context(task_id)
        assert context is not None
        assert context.total_steps == MULTI_STEP_COUNT

        for step_data in steps_data:
            assert step_data["description"] in context.context_summary

        # Complete the task
        completed = await service.update_task_status(task_id, "closed")
        assert completed is True

        # Cleanup
        deleted = await service.delete_task(task_id)
        assert deleted is True
