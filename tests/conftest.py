"""Test configuration and fixtures."""

from pathlib import Path
import sys

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from task_context_mcp.business.services import TaskService
from task_context_mcp.integrations.database.manager import DatabaseManager


@pytest.fixture
async def db_manager():
    """Fixture for test database manager."""
    # Use in-memory SQLite for tests
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
async def task_service():
    """Fixture for unit tests with mocked dependencies."""
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock

    from task_context_mcp.models.value_objects import (
        PaginationInfo,
        TaskListResult,
    )

    # Create mock repositories
    task_repo = AsyncMock()
    step_repo = AsyncMock()

    # Storage for mock data
    tasks = {}
    steps = {}
    next_task_id = 1
    next_step_id = 1

    # Mock task repository methods
    async def mock_save(task):
        nonlocal next_task_id
        if task.id is None:
            task.id = next_task_id
            next_task_id += 1
        tasks[task.id] = task
        return task

    async def mock_get_by_id(task_id):
        return tasks.get(task_id)

    async def mock_get_by_id_with_steps(task_id):
        task = tasks.get(task_id)
        if task:
            task.steps = steps.get(task_id, [])
        return task

    async def mock_list_tasks(filter_criteria=None, page=1, page_size=10):
        all_tasks = list(tasks.values())
        if filter_criteria and filter_criteria.status_filter:
            all_tasks = [
                t for t in all_tasks if t.status == filter_criteria.status_filter
            ]

        if filter_criteria:
            reverse = filter_criteria.sort_order == "desc"
            if filter_criteria.sort_by == "title":
                all_tasks.sort(key=lambda t: t.title, reverse=reverse)
            elif filter_criteria.sort_by == "updated_at":
                all_tasks.sort(key=lambda t: t.updated_at, reverse=reverse)

        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = all_tasks[start:end]

        total_count = len(all_tasks)
        total_pages = (total_count + page_size - 1) // page_size

        return TaskListResult(
            tasks=[task.model_dump() for task in paginated_tasks],
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        )

    async def mock_update_status(task_id, status):
        task = tasks.get(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now(UTC)
            return True
        return False

    async def mock_delete(task_id):
        if task_id in tasks:
            del tasks[task_id]
            steps.pop(task_id, None)
            return True
        return False

    # Mock step repository methods
    async def mock_step_save_batch(steps_list):
        nonlocal next_step_id
        for step in steps_list:
            if step.id is None:
                step.id = next_step_id
                next_step_id += 1
            if step.task_id not in steps:
                steps[step.task_id] = []
            steps[step.task_id].append(step)
        return steps_list

    async def mock_step_update_batch(task_id, updates):
        task_steps = steps.get(task_id, [])
        for update in updates:
            step_name = update["step_name"]
            step = next((s for s in task_steps if s.name == step_name), None)
            if step:
                step.status = update["status"]
                step.description = update.get("description") or step.description
                step.updated_at = update["updated_at"]
        return True

    # Configure mocks
    task_repo.save.side_effect = mock_save
    task_repo.get_by_id.side_effect = mock_get_by_id
    task_repo.get_by_id_with_steps.side_effect = mock_get_by_id_with_steps
    task_repo.list_tasks.side_effect = mock_list_tasks
    task_repo.update_status.side_effect = mock_update_status
    task_repo.delete.side_effect = mock_delete

    step_repo.save_batch.side_effect = mock_step_save_batch
    step_repo.update_batch.side_effect = mock_step_update_batch

    return TaskService(task_repo, step_repo)


@pytest.fixture
async def integration_task_service(db_manager):
    """Fixture for integration tests with real database."""
    from task_context_mcp.integrations.database.repositories import (
        StepRepositoryImpl,
        TaskRepositoryImpl,
    )

    # Create real repositories with session
    session = db_manager.get_session()
    task_repo = TaskRepositoryImpl(session)
    step_repo = StepRepositoryImpl(session)

    # Create service with real dependencies
    return TaskService(task_repo, step_repo)
