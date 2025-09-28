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
        title="Test Task", description="Test Description", project_name="test"
    )

    assert task_id is not None
    assert isinstance(task_id, int)
    assert task_id > 0


@pytest.mark.asyncio
async def test_get_task(task_service):
    """Test getting a task through service."""
    # Create task
    task_id = await task_service.create_task("Test Task", "Test Description", "test")

    # Get task
    task_data = await task_service.get_task(task_id)

    assert task_data is not None
    assert task_data.id == task_id
    assert task_data.title == "Test Task"
    assert task_data.description == "Test Description"
    assert task_data.status == TaskStatus.OPEN


@pytest.mark.asyncio
async def test_create_task_steps(task_service):
    """Test creating steps for a task through service."""
    # Create task
    task_id = await task_service.create_task("Test Task")

    # Create steps
    steps_data = [
        {"step_number": 1, "description": "First step"},
        {"step_number": 2, "description": "Second step"},
    ]
    success = await task_service.create_task_steps(task_id, steps_data)
    assert success is True

    # Get task with steps
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert len(task_data.steps) == 2
    assert task_data.steps[0].name == "Step 1"
    assert task_data.steps[0].description == "First step"


@pytest.mark.asyncio
async def test_update_task_steps(task_service):
    """Test updating existing steps through service."""
    # Create task and steps
    task_id = await task_service.create_task("Test Task")
    await task_service.create_task_steps(
        task_id, [{"step_number": 1, "description": "Original step"}]
    )

    # Update step
    step_updates = [
        {"step_number": 1, "status": "completed", "description": "Updated step"}
    ]
    success = await task_service.update_task_steps(task_id, step_updates)
    assert success is True


@pytest.mark.asyncio
async def test_get_task_context(task_service):
    """Test getting task context through service."""
    # Create task
    task_id = await task_service.create_task("Test Task", "Test Description", "test")

    # Add steps
    await task_service.create_task_steps(
        task_id,
        [
            {"step_number": 1, "description": "Step 1 completed"},
            {"step_number": 2, "description": "Step 2 completed"},
        ],
    )

    # Get context
    context = await task_service.get_task_context(task_id)

    assert context is not None
    assert context.task_id == task_id
    assert context.title == "Test Task"
    assert context.description == "Test Description"
    assert context.total_steps == EXPECTED_TOTAL_STEPS
    assert "Step 1: Step 1 completed" in context.context_summary
    assert "Step 2: Step 2 completed" in context.context_summary


@pytest.mark.asyncio
async def test_list_tasks(task_service):
    """Test listing tasks through service."""
    # Create tasks
    task_id1 = await task_service.create_task("Task 1", project_name="test")
    task_id2 = await task_service.create_task("Task 2", project_name="test")

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
    # Create task with steps
    task_id = await task_service.create_task("Test Task", project_name="test")
    await task_service.create_task_steps(
        task_id, [{"step_number": 1, "description": "Test step"}]
    )

    # Delete task
    success = await task_service.delete_task(task_id)
    assert success is True

    # Verify task is deleted
    task_data = await task_service.get_task(task_id)
    assert task_data is None


@pytest.mark.asyncio
async def test_create_task_steps_nonexistent_task(task_service):
    """Test creating steps for nonexistent task."""
    steps_data = [{"step_number": 1, "description": "Test step"}]
    success = await task_service.create_task_steps(999, steps_data)
    assert success is False


@pytest.mark.asyncio
async def test_update_task_status(task_service):
    """Test updating task status through service."""
    # Create task
    task_id = await task_service.create_task("Test Task", project_name="test")

    # Check initial status
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert task_data.status == TaskStatus.OPEN

    # Complete task
    success = await task_service.update_task_status(task_id, "closed")
    assert success is True

    # Verify status update
    task_data = await task_service.get_task(task_id)
    assert task_data is not None
    assert task_data.status == TaskStatus.CLOSED

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
    success = await task_service.update_task_status(999, "closed")
    assert success is False


@pytest.mark.asyncio
async def test_list_tasks_with_status_filter(task_service):
    """Test filtering tasks by status."""
    # Create tasks
    task_id1 = await task_service.create_task("Open Task", project_name="test")
    task_id2 = await task_service.create_task("Closed Task", project_name="test")

    # Complete one task
    await task_service.update_task_status(task_id2, "closed")

    # Get only open tasks
    result = await task_service.list_tasks(status_filter="open")
    assert len(result.tasks) == 1
    assert result.tasks[0]["id"] == task_id1
    assert result.tasks[0]["status"] == TaskStatus.OPEN

    # Get only closed tasks
    result = await task_service.list_tasks(status_filter="closed")
    assert len(result.tasks) == 1
    assert result.tasks[0]["id"] == task_id2
    assert result.tasks[0]["status"] == TaskStatus.CLOSED

    # Get all tasks
    result = await task_service.list_tasks(status_filter=None)
    assert len(result.tasks) == EXPECTED_TASK_COUNT


@pytest.mark.asyncio
async def test_list_tasks_pagination(task_service):
    """Test task list pagination."""
    # Create 5 tasks
    task_ids = []
    for i in range(5):
        task_id = await task_service.create_task(f"Task {i + 1}", project_name="test")
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
    await task_service.create_task("B Task", project_name="test")
    await task_service.create_task("A Task", project_name="test")
    await task_service.create_task("C Task", project_name="test")

    # Sort by title ascending
    result = await task_service.list_tasks(sort_by="title", sort_order="asc")
    titles = [task["title"] for task in result.tasks]
    assert titles == ["A Task", "B Task", "C Task"]

    # Sort by title descending
    result = await task_service.list_tasks(sort_by="title", sort_order="desc")
    titles = [task["title"] for task in result.tasks]
    assert titles == ["C Task", "B Task", "A Task"]
