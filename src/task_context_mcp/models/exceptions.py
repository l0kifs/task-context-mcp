"""Domain exceptions for the Task Context MCP application."""


class TaskContextError(Exception):
    """Base exception for task context domain errors."""


class TaskNotFoundError(TaskContextError):
    """Raised when a task is not found."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(TaskContextError):
    """Raised when task data validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class TaskStatusError(TaskContextError):
    """Raised when task status operation fails."""

    def __init__(self, task_id: int, message: str):
        self.task_id = task_id
        super().__init__(f"Task {task_id}: {message}")


class SummaryValidationError(TaskContextError):
    """Raised when summary data validation fails."""

    def __init__(self, message: str):
        super().__init__(f"Summary validation error: {message}")


class PaginationError(TaskContextError):
    """Raised when pagination parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(f"Pagination error: {message}")


class DatabaseError(TaskContextError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        self.operation = operation
        super().__init__(f"Database error: {message}")
