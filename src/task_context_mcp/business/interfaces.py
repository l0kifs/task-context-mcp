"""Business logic interfaces and protocols."""

from typing import Protocol

from task_context_mcp.models.entities import Task, TaskSummary
from task_context_mcp.models.value_objects import (
    TaskContext,
    TaskListFilter,
    TaskListResult,
)


class TaskRepository(Protocol):
    """
    Interface for task data access.

    Defines the contract for task persistence operations.
    """

    async def save(self, task: Task) -> Task:
        """Save a task to the repository."""
        ...

    async def get_by_id(self, task_id: int) -> Task | None:
        """Get a task by its ID."""
        ...

    async def get_by_id_with_summaries(self, task_id: int) -> Task | None:
        """Get a task by ID with all its summaries loaded."""
        ...

    async def list_tasks(
        self, filter_criteria: TaskListFilter, page: int = 1, page_size: int = 10
    ) -> TaskListResult:
        """List tasks with filtering and pagination."""
        ...

    async def update_status(self, task_id: int, status: str) -> bool:
        """Update task status. Returns True if updated, False if not found."""
        ...

    async def delete(self, task_id: int) -> bool:
        """Delete a task. Returns True if deleted, False if not found."""
        ...


class TaskSummaryRepository(Protocol):
    """
    Interface for task summary data access.

    Defines the contract for task summary persistence operations.
    """

    async def save(self, summary: TaskSummary) -> TaskSummary:
        """Save a task summary to the repository."""
        ...

    async def get_by_task_and_step(
        self, task_id: int, step_number: int
    ) -> TaskSummary | None:
        """Get a summary by task ID and step number."""
        ...

    async def get_all_by_task_id(self, task_id: int) -> list[TaskSummary]:
        """Get all summaries for a task, ordered by step number."""
        ...


class TaskServiceInterface(Protocol):
    """
    Interface for task business logic operations.

    Defines the contract for task-related business operations.
    """

    async def create_task(self, title: str, description: str | None = None) -> int:
        """Create a new task and return its ID."""
        ...

    async def get_task(self, task_id: int) -> Task | None:
        """Get a task by ID with all its summaries."""
        ...

    async def get_task_context(self, task_id: int) -> TaskContext | None:
        """Get optimized context for task restoration."""
        ...

    async def list_tasks(
        self,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> TaskListResult:
        """List tasks with filtering and pagination."""
        ...

    async def save_summary(self, task_id: int, step_number: int, summary: str) -> bool:
        """
        Save summary for a task step.

        Returns True if saved, False if task not found.
        """
        ...

    async def update_task_status(self, task_id: int, status: str) -> bool:
        """
        Update task status.

        Returns True if updated, False if not found or invalid status.
        """
        ...

    async def delete_task(self, task_id: int) -> bool:
        """
        Delete a task and all its summaries.

        Returns True if deleted, False if not found.
        """
        ...
