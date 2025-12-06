"""Value objects for the Task Context MCP application."""

from pydantic import BaseModel, Field, field_validator

MAX_PAGE_SIZE = 100


class TaskContext(BaseModel):
    """
    Task context for quick restoration.

    This is a value object that contains optimized context information
    for quick task restoration.
    """

    task_id: int = Field(..., gt=0)
    title: str
    description: str | None
    status: str
    total_steps: int = Field(..., ge=0)
    context_summary: str
    last_updated: str


class TaskListFilter(BaseModel):
    """
    Filter criteria for task listing.

    Value object for filtering and sorting task lists.
    """

    status_filter: str | None = None
    project_filter: str | None = None
    sort_by: str = "updated_at"
    sort_order: str = "desc"

    @field_validator("status_filter")
    @classmethod
    def validate_status_filter(cls, v: str | None) -> str | None:
        """Validate status filter."""
        if v is not None and v not in ["open", "in_progress", "closed"]:
            msg = f"Invalid status filter: {v}"
            raise ValueError(msg)
        return v

    @field_validator("project_filter")
    @classmethod
    def validate_project_filter(cls, v: str | None) -> str | None:
        """Validate project filter."""
        if v is not None and not v.strip():
            msg = "Project filter cannot be empty"
            raise ValueError(msg)
        return v.strip() if v else None

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort field."""
        if v not in ["created_at", "updated_at", "title"]:
            msg = f"Invalid sort field: {v}"
            raise ValueError(msg)
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            msg = f"Invalid sort order: {v}"
            raise ValueError(msg)
        return v


class TaskListParams(BaseModel):
    """
    Parameters for task listing with filtering, sorting, and pagination.

    Combines filter criteria and pagination parameters into a single object
    to reduce the number of function arguments.
    """

    status_filter: str | None = None
    project_filter: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=MAX_PAGE_SIZE)
    sort_by: str = "updated_at"
    sort_order: str = "desc"

    @field_validator("status_filter")
    @classmethod
    def validate_status_filter(cls, v: str | None) -> str | None:
        """Validate status filter."""
        if v is not None and v not in ["open", "in_progress", "closed"]:
            msg = f"Invalid status filter: {v}"
            raise ValueError(msg)
        return v

    @field_validator("project_filter")
    @classmethod
    def validate_project_filter(cls, v: str | None) -> str | None:
        """Validate project filter."""
        if v is not None and not v.strip():
            msg = "Project filter cannot be empty"
            raise ValueError(msg)
        return v.strip() if v else None

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort field."""
        if v not in ["created_at", "updated_at", "title"]:
            msg = f"Invalid sort field: {v}"
            raise ValueError(msg)
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            msg = f"Invalid sort order: {v}"
            raise ValueError(msg)
        return v


class PaginationInfo(BaseModel):
    """
    Pagination information for task lists.

    Value object containing pagination metadata.
    """

    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=MAX_PAGE_SIZE)
    total_count: int = Field(..., ge=0)
    total_pages: int
    has_next: bool
    has_prev: bool


class TaskListResult(BaseModel):
    """
    Result of task listing operation.

    Contains tasks and pagination information.
    """

    tasks: list[dict]
    pagination: PaginationInfo
