"""Business logic interfaces and protocols."""

from typing import Protocol

from task_context_mcp.models.entities import Step, Task
from task_context_mcp.models.value_objects import (
    TaskContext,
    TaskListFilter,
    TaskListParams,
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

    async def get_by_id_with_steps(self, task_id: int) -> Task | None:
        """Get a task by ID with all its steps loaded."""
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


class StepRepository(Protocol):
    """
    Interface for step data access.

    Defines the contract for step persistence operations.
    """

    async def save(self, step: Step) -> Step:
        """Save a step to the repository."""
        ...

    async def get_by_id(self, step_id: int) -> Step | None:
        """Get a step by its ID."""
        ...

    async def get_by_task_id(self, task_id: int) -> list[Step]:
        """Get all steps for a task, ordered by creation time."""
        ...

    async def update_status(
        self, step_id: int, status: str, result: str | None = None
    ) -> bool:
        """
        Update step status and optionally result.

        Returns True if updated, False if not found.
        """
        ...

    async def save_batch(self, steps: list[Step]) -> list[Step]:
        """Save multiple steps to the repository."""
        ...

    async def update_batch(self, task_id: int, updates: list[dict]) -> bool:
        """
        Update multiple steps for a task.

        Each update dict should contain 'step_name', 'status',
        'description', 'updated_at'.
        Returns True if all updates successful.
        """
        ...


class TaskServiceInterface(Protocol):
    """
    Interface for task business logic operations.

    Defines the contract for task-related business operations.
    """

    async def create_task(
        self,
        title: str,
        description: str | None = None,
        project_name: str = "default",
        steps: list[dict] | None = None,
    ) -> int:
        """Create a new task and return its ID."""
        ...

    async def get_task(self, task_id: int) -> Task | None:
        """Get a task by ID with all its steps."""
        ...

    async def get_task_context(self, task_id: int) -> TaskContext | None:
        """Get optimized context for task restoration."""
        ...

    async def list_tasks(
        self,
        params: TaskListParams,
    ) -> TaskListResult:
        """List tasks with filtering and pagination."""
        ...

    async def create_task_steps(self, task_id: int, steps: list[dict]) -> bool:
        """
        Create multiple steps for a task.

        Returns True if all steps created, False if task not found.
        """
        ...

    async def update_task_steps(self, task_id: int, steps: list[dict]) -> bool:
        """
        Update existing steps for a task.

        Returns True if all updates successful, False if task not found
        or validation failed.
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
        Delete a task and all its steps.

        Returns True if deleted, False if not found.
        """
        ...
