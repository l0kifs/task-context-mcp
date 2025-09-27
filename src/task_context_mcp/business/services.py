"""Business logic services for task management."""

from datetime import UTC, datetime

from task_context_mcp.business.interfaces import (
    TaskRepository,
    TaskServiceInterface,
    TaskSummaryRepository,
)
from task_context_mcp.config.logging_config import get_logger
from task_context_mcp.models.entities import (
    Task,
    TaskStatus,
    TaskSummary,
)
from task_context_mcp.models.value_objects import (
    TaskContext,
    TaskListFilter,
    TaskListResult,
)

logger = get_logger(__name__)


class TaskService(TaskServiceInterface):
    """
    Business service for task management operations.

    Implements the core business logic for task operations,
    orchestrating between repositories and applying business rules.
    """

    def __init__(
        self, task_repository: TaskRepository, summary_repository: TaskSummaryRepository
    ):
        """
        Initialize the task service.

        Args:
            task_repository: Repository for task data access
            summary_repository: Repository for task summary data access
        """
        self._task_repo = task_repository
        self._summary_repo = summary_repository

    async def create_task(self, title: str, description: str | None = None) -> int:
        """
        Create a new task.

        Applies business rules for task creation and returns the new task ID.

        Args:
            title: Task title (required, non-empty)
            description: Optional task description

        Returns:
            Task ID of the created task

        Raises:
            ValueError: If title is empty or invalid
        """
        logger.info("Creating new task", title=title)

        # Business rule: title cannot be empty
        if not title or not title.strip():
            logger.warning("Attempted to create task with empty title")
            error_msg = "Task title cannot be empty"
            raise ValueError(error_msg)

        # Create task entity
        now = datetime.now(UTC)

        task = Task(
            id=None,  # Will be set by repository
            title=title.strip(),
            description=description.strip() if description else None,
            status=TaskStatus.OPEN,
            created_at=now,
            updated_at=now,
        )

        # Save to repository
        saved_task = await self._task_repo.save(task)

        logger.info("Task created successfully", task_id=saved_task.id, title=title)
        return saved_task.id

    async def get_task(self, task_id: int) -> Task | None:
        """
        Get a task by ID with all its summaries.

        Args:
            task_id: Task identifier

        Returns:
            Task with summaries if found, None otherwise
        """
        logger.debug("Getting task", task_id=task_id)

        task = await self._task_repo.get_by_id_with_summaries(task_id)

        if task:
            logger.debug("Task found", task_id=task_id, title=task.title)
        else:
            logger.debug("Task not found", task_id=task_id)

        return task

    async def get_task_context(self, task_id: int) -> TaskContext | None:
        """
        Get optimized context for task restoration.

        Creates a compact context summary for quick task restoration,
        minimizing token usage while preserving essential information.

        Args:
            task_id: Task identifier

        Returns:
            TaskContext if task exists, None otherwise
        """
        logger.debug("Getting task context", task_id=task_id)

        task = await self._task_repo.get_by_id_with_summaries(task_id)
        if not task:
            logger.debug("Task not found for context", task_id=task_id)
            return None

        # Get all summaries for the task
        summaries = await self._summary_repo.get_all_by_task_id(task_id)

        # Build optimized context summary
        context_summary = self._build_context_summary(summaries)

        context = TaskContext(
            task_id=task.id,
            title=task.title,
            description=task.description,
            total_steps=len(summaries),
            context_summary=context_summary,
            last_updated=task.updated_at.isoformat(),
        )

        logger.debug("Task context built", task_id=task_id, total_steps=len(summaries))
        return context

    async def list_tasks(
        self,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> TaskListResult:
        """
        List tasks with filtering and pagination.

        Args:
            status_filter: Filter by status ("open", "completed", or None for all)
            page: Page number (1-based)
            page_size: Number of tasks per page
            sort_by: Sort field ("created_at", "updated_at", "title")
            sort_order: Sort order ("asc" or "desc")

        Returns:
            TaskListResult with tasks and pagination info
        """
        logger.debug(
            "Listing tasks", status_filter=status_filter, page=page, page_size=page_size
        )

        filter_criteria = TaskListFilter(
            status_filter=status_filter, sort_by=sort_by, sort_order=sort_order
        )

        result = await self._task_repo.list_tasks(filter_criteria, page, page_size)

        logger.debug(
            "Tasks listed", count=len(result.tasks), total=result.pagination.total_count
        )
        return result

    async def save_summary(self, task_id: int, step_number: int, summary: str) -> bool:
        """
        Save summary for a task step.

        If a summary for this step already exists, it will be updated.
        Updates the task's updated_at timestamp.

        Args:
            task_id: Task identifier
            step_number: Step number (must be positive)
            summary: Summary text (cannot be empty)

        Returns:
            True if summary was saved, False if task doesn't exist

        Raises:
            ValueError: If step_number <= 0 or summary is empty
        """
        logger.info("Saving task summary", task_id=task_id, step_number=step_number)

        # Business rules validation
        if step_number <= 0:
            logger.warning(
                "Invalid step number", task_id=task_id, step_number=step_number
            )
            error_msg = "Step number must be positive"
            raise ValueError(error_msg)

        if not summary or not summary.strip():
            logger.warning(
                "Empty summary provided", task_id=task_id, step_number=step_number
            )
            error_msg = "Summary cannot be empty"
            raise ValueError(error_msg)

        # Check if task exists
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            logger.warning("Task not found for summary", task_id=task_id)
            return False

        # Check if summary already exists for this step
        existing_summary = await self._summary_repo.get_by_task_and_step(
            task_id, step_number
        )

        now = datetime.now(UTC)

        if existing_summary:
            # Update existing summary
            existing_summary.summary = summary.strip()
            existing_summary.created_at = now  # Update timestamp
            await self._summary_repo.save(existing_summary)
            logger.info("Summary updated", task_id=task_id, step_number=step_number)
        else:
            # Create new summary
            new_summary = TaskSummary(
                id=None,
                task_id=task_id,
                step_number=step_number,
                summary=summary.strip(),
                created_at=now,
            )
            await self._summary_repo.save(new_summary)
            logger.info("Summary created", task_id=task_id, step_number=step_number)

        # Update task's updated_at timestamp
        await self._task_repo.update_status(
            task_id, task.status
        )  # This will update updated_at

        return True

    async def update_task_status(self, task_id: int, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status ("open" or "completed")

        Returns:
            True if status was updated, False if task doesn't exist or status is invalid

        Raises:
            ValueError: If status is not "open" or "completed"
        """
        logger.info("Updating task status", task_id=task_id, status=status)

        # Business rule: validate status
        if status not in [TaskStatus.OPEN, TaskStatus.COMPLETED]:
            logger.warning("Invalid status provided", task_id=task_id, status=status)
            return False

        # Update status via repository
        updated = await self._task_repo.update_status(task_id, status)

        if updated:
            logger.info("Task status updated", task_id=task_id, status=status)
        else:
            logger.warning("Task not found for status update", task_id=task_id)

        return updated

    async def delete_task(self, task_id: int) -> bool:
        """
        Delete a task and all its summaries.

        This operation is irreversible.

        Args:
            task_id: Task identifier

        Returns:
            True if task was deleted, False if task doesn't exist
        """
        logger.info("Deleting task", task_id=task_id)

        # Check if task exists
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            logger.warning("Task not found for deletion", task_id=task_id)
            return False

        # Delete task (cascade will delete summaries)
        deleted = await self._task_repo.delete(task_id)

        if deleted:
            logger.info("Task deleted", task_id=task_id, title=task.title)
        else:
            logger.error("Failed to delete task", task_id=task_id)

        return deleted

    def _build_context_summary(self, summaries: list[TaskSummary]) -> str:
        """
        Build optimized context summary from task summaries.

        Creates a compact representation suitable for AI context restoration.

        Args:
            summaries: List of task summaries ordered by step number

        Returns:
            Formatted context summary string
        """
        if not summaries:
            return "Задача только создана, шагов пока нет."

        # Sort summaries by step number
        sorted_summaries = sorted(summaries, key=lambda s: s.step_number)

        context_parts = [
            f"Шаг {summary.step_number}: {summary.summary}"
            for summary in sorted_summaries
        ]

        return "\n".join(context_parts)
