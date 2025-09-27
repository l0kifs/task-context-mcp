"""End-to-end tests for critical application scenarios."""

import pytest

from task_context_mcp.business.services import TaskService
from task_context_mcp.integrations.database.repositories import (
    TaskRepositoryImpl,
    TaskSummaryRepositoryImpl,
)
from task_context_mcp.models.entities import TaskStatus

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
        Test complete task lifecycle: create, update, add summary, complete.

        This E2E test covers the critical user journey of managing a task
        from creation to completion.
        """
        # Setup
        await db_manager.initialize()
        task_repo = TaskRepositoryImpl(db_manager.get_session())
        summary_repo = TaskSummaryRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, summary_repo)

        # Step 1: Create a task
        task_id = await service.create_task(
            title="E2E Test Task", description="Testing complete task lifecycle"
        )
        assert task_id is not None

        # Step 2: Get the task and verify creation
        task = await service.get_task(task_id)
        assert task is not None
        assert task.title == "E2E Test Task"
        assert task.status == TaskStatus.OPEN

        # Step 3: Add a summary
        summary_added = await service.save_summary(
            task_id=task_id, step_number=1, summary="Initial analysis completed"
        )
        assert summary_added is True

        # Step 4: Get task context and verify summary
        context = await service.get_task_context(task_id)
        assert context is not None
        assert context.task_id == task_id
        assert context.total_steps == 1
        assert "Initial analysis completed" in context.context_summary

        # Step 5: Update task status to completed
        status_updated = await service.update_task_status(task_id, "completed")
        assert status_updated is True

        # Step 6: Verify final state
        updated_task = await service.get_task(task_id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.COMPLETED

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
        summary_repo = TaskSummaryRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, summary_repo)

        # Create test tasks
        task_ids = []
        for i in range(TASK_COUNT):
            task_id = await service.create_task(
                title=f"Test Task {i}", description=f"Description {i}"
            )
            task_ids.append(task_id)

            # Mark some as completed
            if i >= COMPLETED_THRESHOLD:
                await service.update_task_status(task_id, "completed")

        # Test listing all tasks
        all_tasks = await service.list_tasks()
        assert len(all_tasks.tasks) == TASK_COUNT

        # Test filtering by status
        open_tasks = await service.list_tasks(status_filter="open")
        assert len(open_tasks.tasks) == OPEN_TASK_COUNT

        completed_tasks = await service.list_tasks(status_filter="completed")
        assert len(completed_tasks.tasks) == COMPLETED_TASK_COUNT

        # Test pagination
        paginated = await service.list_tasks(page=1, page_size=PAGE_SIZE)
        assert len(paginated.tasks) == PAGE_SIZE
        assert paginated.pagination.total_count == TASK_COUNT

        # Cleanup
        for task_id in task_ids:
            await service.delete_task(task_id)

    @pytest.mark.asyncio
    async def test_task_with_multiple_summaries(self, db_manager):
        """
        Test task with multiple step summaries.

        This E2E test covers the scenario of tracking task progress
        through multiple steps.
        """
        # Setup
        await db_manager.initialize()
        task_repo = TaskRepositoryImpl(db_manager.get_session())
        summary_repo = TaskSummaryRepositoryImpl(db_manager.get_session())
        service = TaskService(task_repo, summary_repo)

        # Create task
        task_id = await service.create_task(
            title="Multi-step Task", description="Task with multiple progress steps"
        )

        # Add multiple summaries
        steps = [
            "Step 1: Initial planning",
            "Step 2: Implementation started",
            "Step 3: Core functionality complete",
            "Step 4: Testing and validation",
            "Step 5: Final review and completion",
        ]

        for step_num, summary in enumerate(steps, 1):
            added = await service.save_summary(task_id, step_num, summary)
            assert added is True

        # Verify context includes all steps
        context = await service.get_task_context(task_id)
        assert context is not None
        assert context.total_steps == MULTI_STEP_COUNT

        for step in steps:
            assert step in context.context_summary

        # Complete the task
        completed = await service.update_task_status(task_id, "completed")
        assert completed is True

        # Cleanup
        deleted = await service.delete_task(task_id)
        assert deleted is True
