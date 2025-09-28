"""Tests for value objects."""

from pydantic import ValidationError
import pytest

from task_context_mcp.models.value_objects import (
    PaginationInfo,
    TaskContext,
    TaskListFilter,
)


class TestTaskListFilter:
    """Test TaskListFilter value object."""

    def test_create_default_filter(self):
        """Test creating filter with default values."""
        filter_obj = TaskListFilter()

        assert filter_obj.status_filter is None
        assert filter_obj.project_filter is None
        assert filter_obj.sort_by == "updated_at"
        assert filter_obj.sort_order == "desc"

    def test_create_filter_with_all_params(self):
        """Test creating filter with all parameters."""
        filter_obj = TaskListFilter(
            status_filter="open",
            project_filter="my-project",
            sort_by="title",
            sort_order="asc",
        )

        assert filter_obj.status_filter == "open"
        assert filter_obj.project_filter == "my-project"
        assert filter_obj.sort_by == "title"
        assert filter_obj.sort_order == "asc"

    def test_project_filter_validation_valid(self):
        """Test project filter validation with valid values."""
        # Valid non-empty string
        filter_obj = TaskListFilter(project_filter="valid-project")
        assert filter_obj.project_filter == "valid-project"

        # Valid string with whitespace (should be stripped)
        filter_obj = TaskListFilter(project_filter="  spaced-project  ")
        assert filter_obj.project_filter == "spaced-project"

        # None is valid
        filter_obj = TaskListFilter(project_filter=None)
        assert filter_obj.project_filter is None

    def test_project_filter_validation_invalid(self):
        """Test project filter validation with invalid values."""
        # Empty string should raise error
        with pytest.raises(ValidationError, match="Project filter cannot be empty"):
            TaskListFilter(project_filter="")

        # Whitespace-only string should raise error
        with pytest.raises(ValidationError, match="Project filter cannot be empty"):
            TaskListFilter(project_filter="   ")

    def test_status_filter_validation_valid(self):
        """Test status filter validation with valid values."""
        valid_statuses = ["open", "in_progress", "closed", None]

        for status in valid_statuses:
            filter_obj = TaskListFilter(status_filter=status)
            assert filter_obj.status_filter == status

    def test_status_filter_validation_invalid(self):
        """Test status filter validation with invalid values."""
        with pytest.raises(ValidationError, match="Invalid status filter"):
            TaskListFilter(status_filter="invalid_status")

    def test_sort_by_validation_valid(self):
        """Test sort_by validation with valid values."""
        valid_sorts = ["created_at", "updated_at", "title"]

        for sort_by in valid_sorts:
            filter_obj = TaskListFilter(sort_by=sort_by)
            assert filter_obj.sort_by == sort_by

    def test_sort_by_validation_invalid(self):
        """Test sort_by validation with invalid values."""
        with pytest.raises(ValidationError, match="Invalid sort field"):
            TaskListFilter(sort_by="invalid_field")

    def test_sort_order_validation_valid(self):
        """Test sort_order validation with valid values."""
        valid_orders = ["asc", "desc"]

        for sort_order in valid_orders:
            filter_obj = TaskListFilter(sort_order=sort_order)
            assert filter_obj.sort_order == sort_order

    def test_sort_order_validation_invalid(self):
        """Test sort_order validation with invalid values."""
        with pytest.raises(ValidationError, match="Invalid sort order"):
            TaskListFilter(sort_order="invalid_order")

    def test_project_filter_edge_cases(self):
        """Test project filter edge cases."""
        # Single character
        filter_obj = TaskListFilter(project_filter="a")
        assert filter_obj.project_filter == "a"

        # Special characters
        filter_obj = TaskListFilter(project_filter="project-123_test")
        assert filter_obj.project_filter == "project-123_test"

        # Unicode characters
        filter_obj = TaskListFilter(project_filter="проект")
        assert filter_obj.project_filter == "проект"


class TestTaskContext:
    """Test TaskContext value object."""

    def test_create_task_context(self):
        """Test creating TaskContext."""
        context = TaskContext(
            task_id=1,
            title="Test Task",
            description="Test description",
            status="open",
            total_steps=3,
            context_summary="Summary",
            last_updated="2023-01-01T00:00:00",
        )

        assert context.task_id == 1
        assert context.title == "Test Task"
        assert context.description == "Test description"
        assert context.status == "open"
        assert context.total_steps == 3
        assert context.context_summary == "Summary"
        assert context.last_updated == "2023-01-01T00:00:00"

    def test_task_context_validation(self):
        """Test TaskContext validation."""
        # Invalid task_id (must be positive)
        with pytest.raises(ValidationError):
            TaskContext(
                task_id=0,
                title="Test",
                description=None,
                status="open",
                total_steps=0,
                context_summary="Summary",
                last_updated="2023-01-01T00:00:00",
            )

        # Invalid total_steps (must be non-negative)
        with pytest.raises(ValidationError):
            TaskContext(
                task_id=1,
                title="Test",
                description=None,
                status="open",
                total_steps=-1,
                context_summary="Summary",
                last_updated="2023-01-01T00:00:00",
            )


class TestPaginationInfo:
    """Test PaginationInfo value object."""

    def test_create_pagination_info(self):
        """Test creating PaginationInfo."""
        pagination = PaginationInfo(
            page=1,
            page_size=10,
            total_count=25,
            total_pages=3,
            has_next=True,
            has_prev=False,
        )

        assert pagination.page == 1
        assert pagination.page_size == 10
        assert pagination.total_count == 25
        assert pagination.total_pages == 3
        assert pagination.has_next is True
        assert pagination.has_prev is False

    def test_pagination_validation(self):
        """Test PaginationInfo validation."""
        # Invalid page (must be >= 1)
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=0,
                page_size=10,
                total_count=25,
                total_pages=3,
                has_next=True,
                has_prev=False,
            )

        # Invalid page_size (must be >= 1)
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                page_size=0,
                total_count=25,
                total_pages=3,
                has_next=True,
                has_prev=False,
            )

        # Invalid page_size (exceeds MAX_PAGE_SIZE)
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                page_size=101,  # MAX_PAGE_SIZE is 100
                total_count=25,
                total_pages=3,
                has_next=True,
                has_prev=False,
            )

        # Invalid total_count (must be >= 0)
        with pytest.raises(ValidationError):
            PaginationInfo(
                page=1,
                page_size=10,
                total_count=-1,
                total_pages=3,
                has_next=True,
                has_prev=False,
            )
