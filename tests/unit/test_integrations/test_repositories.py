"""Unit tests for integration components with mocks."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from task_context_mcp.integrations.database.models import StepORM
from task_context_mcp.integrations.database.repositories import (
    StepRepositoryImpl,
    TaskRepositoryImpl,
)
from task_context_mcp.models.entities import Step, StepStatus, Task, TaskStatus
from task_context_mcp.models.value_objects import (
    PaginationInfo,
    TaskListFilter,
    TaskListResult,
)


class TestTaskRepositoryImpl:
    """Unit tests for TaskRepositoryImpl with mocked database operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        return AsyncMock()

    @pytest.fixture
    def task_repository(self, mock_session):
        """Create TaskRepositoryImpl with mocked session."""
        return TaskRepositoryImpl(mock_session)

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id=1,
            title="Test Task",
            description="Test Description",
            project_name="test",
            status=TaskStatus.OPEN,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_repository_initialization(self, mock_session):
        """Test that repository can be initialized."""
        repository = TaskRepositoryImpl(mock_session)
        # Test that session is properly assigned (accessing private member for testing)
        assert hasattr(repository, "_session")

    @pytest.mark.asyncio
    async def test_save_task_success(self, task_repository, mock_session, sample_task):
        """Test successful task saving."""
        # Setup mock for existing task update path (since sample_task has id=1)
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = sample_task.title
        mock_task_orm.description = sample_task.description
        mock_task_orm.project_name = sample_task.project_name
        mock_task_orm.status = sample_task.status
        mock_task_orm.created_at = sample_task.created_at
        mock_task_orm.updated_at = sample_task.updated_at

        # Mock the database query result for update path
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm

        # Mock the session operations
        mock_session.execute.return_value = mock_result
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Execute
        result = await task_repository.save(sample_task)

        # Verify
        assert result.id == 1
        assert result.title == sample_task.title
        assert result.status == sample_task.status
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, task_repository, mock_session):
        """Test getting task by ID when found."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.project_name = "test"
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.get_by_id(1)

        # Verify
        assert result is not None
        assert result.id == 1
        assert result.title == "Test Task"
        assert result.status == TaskStatus.OPEN
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, task_repository, mock_session):
        """Test getting task by ID when not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.get_by_id(999)

        # Verify
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_with_steps(self, task_repository, mock_session):
        """Test getting task with steps loaded."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.project_name = "test"
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.get_by_id_with_steps(1)

        # Verify
        assert result is not None
        assert result.id == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_with_filter(self, task_repository, mock_session):
        """Test listing tasks with filtering and pagination."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.project_name = "test"
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock task query result
        mock_task_result = MagicMock()
        mock_task_result.scalars.return_value.all.return_value = [mock_task_orm]

        mock_session.execute.side_effect = [mock_count_result, mock_task_result]

        # Setup filter
        filter_criteria = TaskListFilter(
            status_filter=TaskStatus.OPEN, sort_by="updated_at", sort_order="desc"
        )

        # Execute
        result = await task_repository.list_tasks(filter_criteria, page=1, page_size=10)

        # Verify
        assert isinstance(result, TaskListResult)
        assert len(result.tasks) == 1
        assert isinstance(result.pagination, PaginationInfo)
        assert result.pagination.total_count == 1
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10

    @pytest.mark.asyncio
    async def test_list_tasks_with_project_filter(self, task_repository, mock_session):
        """Test listing tasks with project filter."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.project_name = "specific-project"
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock task query result
        mock_task_result = MagicMock()
        mock_task_result.scalars.return_value.all.return_value = [mock_task_orm]

        mock_session.execute.side_effect = [mock_count_result, mock_task_result]

        # Setup filter with project filter
        filter_criteria = TaskListFilter(
            project_filter="specific-project", sort_by="updated_at", sort_order="desc"
        )

        # Execute
        result = await task_repository.list_tasks(filter_criteria, page=1, page_size=10)

        # Verify
        assert isinstance(result, TaskListResult)
        assert len(result.tasks) == 1
        assert result.tasks[0]["project_name"] == "specific-project"
        assert isinstance(result.pagination, PaginationInfo)
        assert result.pagination.total_count == 1

        # Verify that the session was called twice (count query and task query)
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_tasks_with_combined_filters(
        self, task_repository, mock_session
    ):
        """Test listing tasks with both status and project filters."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.project_name = "specific-project"
        mock_task_orm.status = TaskStatus.CLOSED
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock task query result
        mock_task_result = MagicMock()
        mock_task_result.scalars.return_value.all.return_value = [mock_task_orm]

        mock_session.execute.side_effect = [mock_count_result, mock_task_result]

        # Setup filter with both filters
        filter_criteria = TaskListFilter(
            status_filter=TaskStatus.CLOSED,
            project_filter="specific-project",
            sort_by="updated_at",
            sort_order="desc",
        )

        # Execute
        result = await task_repository.list_tasks(filter_criteria, page=1, page_size=10)

        # Verify
        assert isinstance(result, TaskListResult)
        assert len(result.tasks) == 1
        assert result.tasks[0]["project_name"] == "specific-project"
        assert result.tasks[0]["status"] == TaskStatus.CLOSED
        assert isinstance(result.pagination, PaginationInfo)
        assert result.pagination.total_count == 1

        # Verify that the session was called twice (count query and task query)
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_status_success(self, task_repository, mock_session):
        """Test successful status update."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.update_status(1, TaskStatus.CLOSED)

        # Verify
        assert result is True
        assert mock_task_orm.status == TaskStatus.CLOSED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, task_repository, mock_session):
        """Test status update when task not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.update_status(999, TaskStatus.CLOSED)

        # Verify
        assert result is False
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_success(self, task_repository, mock_session):
        """Test successful task deletion."""
        # Setup mock
        mock_task_orm = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.delete(1)

        # Verify
        assert result is True
        mock_session.delete.assert_called_once_with(mock_task_orm)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, task_repository, mock_session):
        """Test deletion when task not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


class TestStepRepositoryImpl:
    """Unit tests for StepRepositoryImpl with mocked database operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        return AsyncMock()

    @pytest.fixture
    def step_repository(self, mock_session):
        """Create StepRepositoryImpl with mocked session."""
        return StepRepositoryImpl(mock_session)

    @pytest.fixture
    def sample_step(self):
        """Create a sample step for testing."""
        return Step(
            id=1,
            task_id=1,
            name="Step 1",
            description="Test step",
            status=StepStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_repository_initialization(self, mock_session):
        """Test that repository can be initialized."""
        repository = StepRepositoryImpl(mock_session)
        # Test that session is properly assigned (accessing private member for testing)
        assert hasattr(repository, "_session")

    @pytest.mark.asyncio
    async def test_save_batch_success(self, step_repository, mock_session, sample_step):
        """Test successful batch step saving."""
        # Setup mock
        mock_step_orm = MagicMock()
        mock_step_orm.id = 1
        mock_step_orm.task_id = sample_step.task_id
        mock_step_orm.name = sample_step.name
        mock_step_orm.description = sample_step.description
        mock_step_orm.status = sample_step.status
        mock_step_orm.result = sample_step.result
        mock_step_orm.created_at = sample_step.created_at
        mock_step_orm.updated_at = sample_step.updated_at

        # Mock the session operations
        mock_session.add_all.return_value = None
        mock_session.commit.return_value = None

        # Mock the ORM constructor
        with (
            patch.object(StepORM, "__init__", return_value=None),
            patch.object(StepORM, "__new__", return_value=mock_step_orm),
        ):
            # Execute
            result = await step_repository.save_batch([sample_step])

            # Verify
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].task_id == sample_step.task_id
            assert result[0].name == sample_step.name
            mock_session.add_all.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_batch_success(self, step_repository, mock_session):
        """Test successful batch step updates."""
        # Setup mock
        mock_step_orm = MagicMock()
        mock_step_orm.name = "Step 1"
        mock_step_orm.status = StepStatus.PENDING
        mock_step_orm.updated_at = datetime.now(UTC)

        # Mock the execute result - scalar_one_or_none should return the mock object
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_step_orm
        mock_session.execute.return_value = mock_result

        updates = [
            {
                "step_name": "Step 1",
                "status": StepStatus.COMPLETED,
                "description": "Updated description",
                "updated_at": datetime.now(UTC),
            }
        ]

        # Execute
        result = await step_repository.update_batch(1, updates)

        # Verify
        assert result is True
        assert mock_step_orm.status == StepStatus.COMPLETED
        assert mock_step_orm.description == "Updated description"
        mock_session.commit.assert_called_once()
