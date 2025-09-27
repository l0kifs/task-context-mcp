"""Tests for business services."""

from pathlib import Path
import sys

import pytest

from task_context_mcp.models.entities import TaskStatus

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test constants
EXPECTED_TASK_COUNT = 2
EXPECTED_TOTAL_STEPS = 2
EXPECTED_PAGE_SIZE = 2
EXPECTED_TOTAL_COUNT = 5
EXPECTED_TOTAL_PAGES = 3
EXPECTED_PAGE_TWO = 2
EXPECTED_PAGE_THREE = 3


@pytest.mark.asyncio
async def test_create_task(task_service):
    """Test creating a task through service."""
    task_id = await task_service.create_task(
        title="Test Task", description="Test Description"
    )

    assert task_id is not None
    assert isinstance(task_id, int)
    assert task_id > 0


@pytest.mark.asyncio
async def test_get_task(task_service):
    """Test getting a task through service."""
    # Create task
    task_id = await task_service.create_task("Test Task", "Test Description")

    # Get task
    task_data = await task_service.get_task(task_id)

    assert task_data is not None
    assert task_data.id == task_id
    assert task_data.title == "Test Task"
    assert task_data.description == "Test Description"
    assert task_data.status == TaskStatus.OPEN


@pytest.mark.asyncio
async def test_save_and_get_summary(task_service):
    """Test saving and getting summary through service."""
    # Create task
    task_id = await task_service.create_task("Test Task")

    # Save summary
    success = await task_service.save_summary(task_id, 1, "Test summary for step 1")
    assert success is True

    # Get task with summary
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    # Note: summaries are loaded via repository, not directly accessible here


@pytest.mark.asyncio
async def test_update_existing_summary(task_service):
    """Test updating existing summary through service."""
    # Create task and summary
    task_id = await task_service.create_task("Test Task")
    await task_service.save_summary(task_id, 1, "Original summary")

    # Update summary
    success = await task_service.save_summary(task_id, 1, "Updated summary")
    assert success is True


@pytest.mark.asyncio
async def test_get_task_context(task_service):
    """Test getting task context through service."""
    # Create task
    task_id = await task_service.create_task("Test Task", "Test Description")

    # Add summaries
    await task_service.save_summary(task_id, 1, "Step 1 completed")
    await task_service.save_summary(task_id, 2, "Step 2 completed")

    # Get context
    context = await task_service.get_task_context(task_id)

    assert context is not None
    assert context.task_id == task_id
    assert context.title == "Test Task"
    assert context.description == "Test Description"
    assert context.total_steps == EXPECTED_TOTAL_STEPS
    assert "Шаг 1: Step 1 completed" in context.context_summary
    assert "Шаг 2: Step 2 completed" in context.context_summary


@pytest.mark.asyncio
async def test_list_tasks(task_service):
    """Test listing tasks through service."""
    # Create tasks
    task_id1 = await task_service.create_task("Task 1")
    task_id2 = await task_service.create_task("Task 2")

    # List tasks
    result = await task_service.list_tasks()

    assert result.tasks is not None
    assert len(result.tasks) == EXPECTED_TASK_COUNT
    assert result.pagination.total_count == EXPECTED_TASK_COUNT
    assert result.pagination.page == 1

    task_ids = [task["id"] for task in result.tasks if task["id"] is not None]
    assert task_id1 in task_ids
    assert task_id2 in task_ids

    # Check default status
    for task in result.tasks:
        assert task["status"] == TaskStatus.OPEN


@pytest.mark.asyncio
async def test_delete_task(task_service):
    """Test deleting a task through service."""
    # Create task with summary
    task_id = await task_service.create_task("Test Task")
    await task_service.save_summary(task_id, 1, "Test summary")

    # Delete task
    success = await task_service.delete_task(task_id)
    assert success is True

    # Verify task is deleted
    task_data = await task_service.get_task(task_id)
    assert task_data is None


@pytest.mark.asyncio
async def test_save_summary_nonexistent_task(task_service):
    """Test saving summary for nonexistent task."""
    success = await task_service.save_summary(999, 1, "Test summary")
    assert success is False


@pytest.mark.asyncio
async def test_update_task_status(task_service):
    """Test updating task status through service."""
    # Create task
    task_id = await task_service.create_task("Test Task")

    # Check initial status
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert task_data.status == TaskStatus.OPEN

    # Complete task
    success = await task_service.update_task_status(task_id, "completed")
    assert success is True

    # Verify status update
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert task_data.status == TaskStatus.COMPLETED

    # Reopen task
    success = await task_service.update_task_status(task_id, "open")
    assert success is True

    # Verify status
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert task_data.status == TaskStatus.OPEN


@pytest.mark.asyncio
async def test_update_task_status_invalid(task_service):
    """Test updating task status with invalid data."""
    # Create task
    task_id = await task_service.create_task("Test Task")

    # Try invalid status
    success = await task_service.update_task_status(task_id, "invalid")
    assert success is False

    # Try nonexistent task
    success = await task_service.update_task_status(999, "completed")
    assert success is False


@pytest.mark.asyncio
async def test_list_tasks_with_status_filter(task_service):
    """Test filtering tasks by status."""
    # Create tasks
    task_id1 = await task_service.create_task("Open Task")
    task_id2 = await task_service.create_task("Completed Task")

    # Complete one task
    await task_service.update_task_status(task_id2, "completed")

    # Get only open tasks
    result = await task_service.list_tasks(status_filter="open")
    assert len(result.tasks) == 1
    assert result.tasks[0]["id"] == task_id1
    assert result.tasks[0]["status"] == TaskStatus.OPEN

    # Get only completed tasks
    result = await task_service.list_tasks(status_filter="completed")
    assert len(result.tasks) == 1
    assert result.tasks[0]["id"] == task_id2
    assert result.tasks[0]["status"] == TaskStatus.COMPLETED

    # Get all tasks
    result = await task_service.list_tasks(status_filter=None)
    assert len(result.tasks) == EXPECTED_TASK_COUNT


@pytest.mark.asyncio
async def test_list_tasks_pagination(task_service):
    """Test task list pagination."""
    # Create 5 tasks
    task_ids = []
    for i in range(5):
        task_id = await task_service.create_task(f"Task {i + 1}")
        task_ids.append(task_id)

    # Get first page (2 tasks)
    result = await task_service.list_tasks(page=1, page_size=EXPECTED_PAGE_SIZE)
    assert len(result.tasks) == EXPECTED_PAGE_SIZE
    assert result.pagination.page == 1
    assert result.pagination.page_size == EXPECTED_PAGE_SIZE
    assert result.pagination.total_count == EXPECTED_TOTAL_COUNT
    assert result.pagination.total_pages == EXPECTED_TOTAL_PAGES
    assert result.pagination.has_next is True
    assert result.pagination.has_prev is False

    # Get second page
    result = await task_service.list_tasks(
        page=EXPECTED_PAGE_TWO, page_size=EXPECTED_PAGE_SIZE
    )
    assert len(result.tasks) == EXPECTED_PAGE_SIZE
    assert result.pagination.page == EXPECTED_PAGE_TWO
    assert result.pagination.has_next is True
    assert result.pagination.has_prev is True

    # Get last page
    result = await task_service.list_tasks(
        page=EXPECTED_PAGE_THREE, page_size=EXPECTED_PAGE_SIZE
    )
    assert len(result.tasks) == 1
    assert result.pagination.page == EXPECTED_PAGE_THREE
    assert result.pagination.has_next is False
    assert result.pagination.has_prev is True


@pytest.mark.asyncio
async def test_list_tasks_sorting(task_service):
    """Test task list sorting."""
    # Create tasks with different titles
    await task_service.create_task("B Task")
    await task_service.create_task("A Task")
    await task_service.create_task("C Task")

    # Sort by title ascending
    result = await task_service.list_tasks(sort_by="title", sort_order="asc")
    titles = [task["title"] for task in result.tasks]
    assert titles == ["A Task", "B Task", "C Task"]

    # Sort by title descending
    result = await task_service.list_tasks(sort_by="title", sort_order="desc")
    titles = [task["title"] for task in result.tasks]
    assert titles == ["C Task", "B Task", "A Task"]
