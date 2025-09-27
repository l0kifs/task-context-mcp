"""Unit tests for integration components with mocks."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from task_context_mcp.integrations.database.models import TaskORM, TaskSummaryORM
from task_context_mcp.integrations.database.repositories import (
    TaskRepositoryImpl,
    TaskSummaryRepositoryImpl,
)
from task_context_mcp.models.entities import Task, TaskStatus, TaskSummary
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
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = sample_task.title
        mock_task_orm.description = sample_task.description
        mock_task_orm.status = sample_task.status
        mock_task_orm.created_at = sample_task.created_at
        mock_task_orm.updated_at = sample_task.updated_at

        # Mock the session operations
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Mock the ORM constructor
        with (
            patch.object(TaskORM, "__init__", return_value=None),
            patch.object(TaskORM, "__new__", return_value=mock_task_orm),
        ):
            # Execute
            result = await task_repository.save(sample_task)

            # Verify
            assert result.id == 1
            assert result.title == sample_task.title
            assert result.status == sample_task.status
            mock_session.add.assert_called_once()
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
    async def test_get_by_id_with_summaries(self, task_repository, mock_session):
        """Test getting task with summaries loaded."""
        # Setup mock
        mock_task_orm = MagicMock()
        mock_task_orm.id = 1
        mock_task_orm.title = "Test Task"
        mock_task_orm.description = "Test Description"
        mock_task_orm.status = TaskStatus.OPEN
        mock_task_orm.created_at = datetime.now(UTC)
        mock_task_orm.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.get_by_id_with_summaries(1)

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
        result = await task_repository.update_status(1, TaskStatus.COMPLETED)

        # Verify
        assert result is True
        assert mock_task_orm.status == TaskStatus.COMPLETED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, task_repository, mock_session):
        """Test status update when task not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await task_repository.update_status(999, TaskStatus.COMPLETED)

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


class TestTaskSummaryRepositoryImpl:
    """Unit tests for TaskSummaryRepositoryImpl with mocked database operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        return AsyncMock()

    @pytest.fixture
    def summary_repository(self, mock_session):
        """Create TaskSummaryRepositoryImpl with mocked session."""
        return TaskSummaryRepositoryImpl(mock_session)

    @pytest.fixture
    def sample_summary(self):
        """Create a sample task summary for testing."""
        return TaskSummary(
            id=1,
            task_id=1,
            step_number=1,
            summary="Test summary",
            created_at=datetime.now(UTC),
        )

    def test_repository_initialization(self, mock_session):
        """Test that repository can be initialized."""
        repository = TaskSummaryRepositoryImpl(mock_session)
        # Test that session is properly assigned (accessing private member for testing)
        assert hasattr(repository, "_session")

    async def test_save_summary_success(
        self, summary_repository, mock_session, sample_summary
    ):
        """Test successful summary saving."""
        # Setup mock
        mock_summary_orm = MagicMock()
        mock_summary_orm.id = 1
        mock_summary_orm.task_id = sample_summary.task_id
        mock_summary_orm.step_number = sample_summary.step_number
        mock_summary_orm.summary = sample_summary.summary
        mock_summary_orm.created_at = sample_summary.created_at

        # Mock the session operations
        mock_session.merge.return_value = mock_summary_orm
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Mock the ORM constructor
        with (
            patch.object(TaskSummaryORM, "__init__", return_value=None),
            patch.object(TaskSummaryORM, "__new__", return_value=mock_summary_orm),
        ):
            # Execute
            result = await summary_repository.save(sample_summary)

            # Verify
            assert result.id == 1
            assert result.task_id == sample_summary.task_id
            assert result.step_number == sample_summary.step_number
            mock_session.merge.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_task_and_step_found(self, summary_repository, mock_session):
        """Test getting summary by task ID and step when found."""
        # Setup mock
        mock_summary_orm = MagicMock()
        mock_summary_orm.id = 1
        mock_summary_orm.task_id = 1
        mock_summary_orm.step_number = 1
        mock_summary_orm.summary = "Test summary"
        mock_summary_orm.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_summary_orm
        mock_session.execute.return_value = mock_result

        # Execute
        result = await summary_repository.get_by_task_and_step(1, 1)

        # Verify
        assert result is not None
        assert result.id == 1
        assert result.task_id == 1
        assert result.step_number == 1
        mock_session.execute.assert_called_once()

    async def test_get_by_task_and_step_not_found(
        self, summary_repository, mock_session
    ):
        """Test getting summary by task ID and step when not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await summary_repository.get_by_task_and_step(1, 999)

        # Verify
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_by_task_id(self, summary_repository, mock_session):
        """Test getting all summaries for a task."""
        # Setup mock
        mock_summary_orm1 = MagicMock()
        mock_summary_orm1.id = 1
        mock_summary_orm1.task_id = 1
        mock_summary_orm1.step_number = 1
        mock_summary_orm1.summary = "Summary 1"
        mock_summary_orm1.created_at = datetime.now(UTC)

        mock_summary_orm2 = MagicMock()
        mock_summary_orm2.id = 2
        mock_summary_orm2.task_id = 1
        mock_summary_orm2.step_number = 2
        mock_summary_orm2.summary = "Summary 2"
        mock_summary_orm2.created_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_summary_orm1,
            mock_summary_orm2,
        ]
        mock_session.execute.return_value = mock_result

        # Execute
        result = await summary_repository.get_all_by_task_id(1)

        # Verify
        assert len(result) == 2
        assert result[0].step_number == 1
        assert result[1].step_number == 2
        assert result[0].task_id == 1
        assert result[1].task_id == 1
        mock_session.execute.assert_called_once()
