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

    from src.task_context_mcp.models.value_objects import (
        PaginationInfo,
        TaskListResult,
    )

    # Create mock repositories
    task_repo = AsyncMock()
    summary_repo = AsyncMock()

    # Storage for mock data
    tasks = {}
    summaries = {}
    next_task_id = 1

    # Mock task repository methods with dynamic behavior
    async def mock_save(task):
        nonlocal next_task_id
        if task.id is None:
            task.id = next_task_id
            next_task_id += 1
        tasks[task.id] = task
        return task

    async def mock_get_by_id(task_id):
        return tasks.get(task_id)

    async def mock_get_by_id_with_summaries(task_id):
        task = tasks.get(task_id)
        if task:
            # Add summaries to task if they exist
            task.summaries = summaries.get(task_id, [])
        return task

    async def mock_list_tasks(filter_criteria=None, page=1, page_size=10):
        all_tasks = list(tasks.values())
        # Simple filtering by status if provided
        if filter_criteria and filter_criteria.status_filter:
            all_tasks = [
                t for t in all_tasks if t.status == filter_criteria.status_filter
            ]

        # Simple sorting
        if filter_criteria:
            if filter_criteria.sort_by == "title":
                reverse = filter_criteria.sort_order == "desc"
                all_tasks.sort(key=lambda t: t.title, reverse=reverse)
            elif filter_criteria.sort_by == "updated_at":
                reverse = filter_criteria.sort_order == "desc"
                all_tasks.sort(key=lambda t: t.updated_at, reverse=reverse)

        # Simple pagination
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
            summaries.pop(task_id, None)  # Also delete summaries
            return True
        return False

    # Mock summary repository methods
    async def mock_summary_save(summary):
        if summary.id is None:
            summary.id = (
                len(
                    [s for task_summaries in summaries.values() for s in task_summaries]
                )
                + 1
            )
        if summary.task_id not in summaries:
            summaries[summary.task_id] = []
        summaries[summary.task_id].append(summary)
        return summary

    async def mock_get_by_task_and_step(task_id, step_number):
        task_summaries = summaries.get(task_id, [])
        return next((s for s in task_summaries if s.step_number == step_number), None)

    async def mock_get_all_by_task_id(task_id):
        return summaries.get(task_id, [])

    # Configure mocks
    task_repo.save.side_effect = mock_save
    task_repo.get_by_id.side_effect = mock_get_by_id
    task_repo.get_by_id_with_summaries.side_effect = mock_get_by_id_with_summaries
    task_repo.list_tasks.side_effect = mock_list_tasks
    task_repo.update_status.side_effect = mock_update_status
    task_repo.delete.side_effect = mock_delete

    summary_repo.save.side_effect = mock_summary_save
    summary_repo.get_by_task_and_step.side_effect = mock_get_by_task_and_step
    summary_repo.get_all_by_task_id.side_effect = mock_get_all_by_task_id

    # Create service with mocked dependencies
    return TaskService(task_repo, summary_repo)


@pytest.fixture
async def integration_task_service(db_manager):
    """Fixture for integration tests with real database."""
    from src.task_context_mcp.integrations.database.repositories import (
        TaskRepositoryImpl,
        TaskSummaryRepositoryImpl,
    )

    # Create real repositories with session
    session = db_manager.get_session()
    task_repo = TaskRepositoryImpl(session)
    task_summary_repo = TaskSummaryRepositoryImpl(session)

    # Create service with real dependencies
    return TaskService(task_repo, task_summary_repo)
