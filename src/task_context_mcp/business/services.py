"""Business logic services for task management."""

from datetime import UTC, datetime

from task_context_mcp.business.interfaces import (
    StepRepository,
    TaskRepository,
    TaskServiceInterface,
)
from task_context_mcp.config.logging_config import get_logger
from task_context_mcp.models.entities import (
    Step,
    StepStatus,
    Task,
    TaskStatus,
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
        self, task_repository: TaskRepository, step_repository: StepRepository
    ):
        """
        Initialize the task service.

        Args:
            task_repository: Repository for task data access
            step_repository: Repository for step data access
        """
        self._task_repo = task_repository
        self._step_repo = step_repository

    async def create_task(
        self,
        title: str,
        description: str | None = None,
        project_name: str = "default",
        steps: list[dict] | None = None,
    ) -> int:
        """
        Create a new task.

        Applies business rules for task creation and returns the new task ID.

        Args:
            title: Task title (required, non-empty)
            description: Optional task description
            project_name: Project name (required, non-empty)
            steps: Optional list of steps to create with the task. Each step dict contains:
                - name: Step name (required)
                - description: Step description (optional)

        Returns:
            Task ID of the created task

        Raises:
            ValueError: If title or project_name is empty or invalid
        """
        logger.info(
            "Creating new task",
            title=title,
            project_name=project_name,
            steps_count=len(steps) if steps else 0,
        )

        # Business rule: title cannot be empty
        if not title or not title.strip():
            logger.warning("Attempted to create task with empty title")
            error_msg = "Task title cannot be empty"
            raise ValueError(error_msg)

        # Business rule: project_name cannot be empty
        if not project_name or not project_name.strip():
            logger.warning("Attempted to create task with empty project_name")
            error_msg = "Task project_name cannot be empty"
            raise ValueError(error_msg)

        # Create task entity
        now = datetime.now(UTC)

        task = Task(
            id=None,  # Will be set by repository
            title=title.strip(),
            description=description.strip() if description else None,
            project_name=project_name.strip(),
            status=TaskStatus.OPEN,
            created_at=now,
            updated_at=now,
        )

        # Save to repository
        saved_task = await self._task_repo.save(task)

        # Create steps if provided
        if steps:
            await self._create_steps_for_task(saved_task.id, steps)

        logger.info(
            "Task created successfully",
            task_id=saved_task.id,
            title=title,
            steps_count=len(steps) if steps else 0,
        )
        return saved_task.id

    async def get_task(self, task_id: int) -> Task | None:
        """
        Get a task by ID with all its steps.

        Args:
            task_id: Task identifier

        Returns:
            Task with steps if found, None otherwise
        """
        logger.debug("Getting task", task_id=task_id)

        task = await self._task_repo.get_by_id_with_steps(task_id)

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

        task = await self._task_repo.get_by_id_with_steps(task_id)
        if not task:
            logger.debug("Task not found for context", task_id=task_id)
            return None

        # Build optimized context summary from steps
        context_summary = self._build_context_summary_from_steps(task.steps)

        context = TaskContext(
            task_id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            total_steps=len(task.steps),
            context_summary=context_summary,
            last_updated=task.updated_at.isoformat(),
        )

        logger.debug("Task context built", task_id=task_id, total_steps=len(task.steps))
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

    async def create_task_steps(self, task_id: int, steps_data: list[dict]) -> bool:
        """
        Create multiple steps for a task.

        Args:
            task_id: Task identifier
            steps_data: List of step data dicts with 'step_number' and 'description'

        Returns:
            True if steps were created, False if task doesn't exist

        Raises:
            ValueError: If step data is invalid
        """
        logger.info("Creating task steps", task_id=task_id, steps_count=len(steps_data))

        # Check if task exists
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            logger.warning("Task not found for step creation", task_id=task_id)
            return False

        # Validate step data
        for step_data in steps_data:
            step_number = step_data.get("step_number")
            description = step_data.get("description")

            if not isinstance(step_number, int) or step_number <= 0:
                error_msg = f"Invalid step number: {step_number}"
                raise ValueError(error_msg)

            if not description or not description.strip():
                error_msg = f"Empty description for step {step_number}"
                raise ValueError(error_msg)

        # Create steps
        now = datetime.now(UTC)
        steps = []

        for step_data in steps_data:
            step = Step(
                id=None,
                task_id=task_id,
                name=f"Step {step_data['step_number']}",
                description=step_data["description"].strip(),
                status=StepStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            steps.append(step)

        # Save all steps
        await self._step_repo.save_batch(steps)

        # Update task's updated_at timestamp
        await self._task_repo.update_status(task_id, task.status)

        logger.info("Task steps created", task_id=task_id, steps_count=len(steps))
        return True

    async def update_task_steps(self, task_id: int, step_updates: list[dict]) -> bool:
        """
        Update multiple steps for a task.

        Args:
            task_id: Task identifier
            step_updates: List of step update dicts with 'step_number',
            'status', and optional 'description'

        Returns:
            True if steps were updated, False if task doesn't exist

        Raises:
            ValueError: If step update data is invalid
        """
        logger.info(
            "Updating task steps", task_id=task_id, updates_count=len(step_updates)
        )

        # Check if task exists
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            logger.warning("Task not found for step updates", task_id=task_id)
            return False

        # Validate and collect updates
        updates = []
        now = datetime.now(UTC)

        for update_data in step_updates:
            step_number = update_data.get("step_number")
            status = update_data.get("status")
            description = update_data.get("description")

            if not isinstance(step_number, int) or step_number <= 0:
                error_msg = f"Invalid step number: {step_number}"
                raise ValueError(error_msg)

            valid_statuses = [
                StepStatus.PENDING,
                StepStatus.COMPLETED,
                StepStatus.CANCELLED,
            ]
            if status not in valid_statuses:
                error_msg = f"Invalid status for step {step_number}: {status}"
                raise ValueError(error_msg)

            updates.append(
                {
                    "step_name": f"Step {step_number}",
                    "status": status,
                    "description": description.strip() if description else None,
                    "updated_at": now,
                }
            )

        # Update steps
        await self._step_repo.update_batch(task_id, updates)

        # Update task's updated_at timestamp
        await self._task_repo.update_status(task_id, task.status)

        logger.info("Task steps updated", task_id=task_id, updates_count=len(updates))
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
        valid_statuses = [TaskStatus.OPEN, TaskStatus.IN_PROGRESS, TaskStatus.CLOSED]
        if status not in valid_statuses:
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

    async def _create_steps_for_task(
        self, task_id: int, steps_data: list[dict]
    ) -> None:
        """
        Create multiple steps for a newly created task.

        Args:
            task_id: Task identifier
            steps_data: List of step data dicts with 'name' and 'description'

        Raises:
            ValueError: If step data is invalid
        """
        logger.debug(
            "Creating steps for new task", task_id=task_id, steps_count=len(steps_data)
        )

        # Validate step data
        for step_data in steps_data:
            name = step_data.get("name")
            description = step_data.get("description")

            if not name or not name.strip():
                error_msg = f"Step name cannot be empty: {step_data}"
                raise ValueError(error_msg)

            if not description or not description.strip():
                error_msg = f"Step description cannot be empty: {step_data}"
                raise ValueError(error_msg)

        # Create steps
        now = datetime.now(UTC)
        steps = []

        for step_data in steps_data:
            step = Step(
                id=None,
                task_id=task_id,
                name=step_data["name"].strip(),
                description=step_data["description"].strip(),
                status=StepStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            steps.append(step)

        # Save all steps
        await self._step_repo.save_batch(steps)

        logger.debug(
            "Steps created for new task", task_id=task_id, steps_count=len(steps)
        )

    def _build_context_summary_from_steps(self, steps: list[Step]) -> str:
        """
        Build optimized context summary from task steps.

        Creates a compact representation suitable for AI context restoration.

        Args:
            steps: List of task steps

        Returns:
            Formatted context summary string
        """
        if not steps:
            return "Задача только создана, шагов пока нет."

        # Sort steps by name (which includes step number)
        sorted_steps = sorted(steps, key=lambda s: s.name)

        context_parts = []
        for step in sorted_steps:
            status_emoji = {
                StepStatus.PENDING: "⏳",
                StepStatus.COMPLETED: "✅",
                StepStatus.CANCELLED: "❌",
            }.get(step.status, "❓")

            result_part = f" ({step.result})" if step.result else ""
            step_line = f"{status_emoji} {step.name}: {step.description}{result_part}"
            context_parts.append(step_line)

        return "\n".join(context_parts)

    async def get_task_with_steps(self, task_id: int) -> dict | None:
        """
        Get a task with all its steps.

        Args:
            task_id: Task identifier

        Returns:
            Dict with task and steps data, or None if not found
        """
        logger.debug("Getting task with steps", task_id=task_id)

        # Get task
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            return None

        # Get steps
        steps = await self._step_repo.get_by_task_id(task_id)

        # Convert to dict format
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "project_name": task.project_name,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

        steps_list = []
        for step in steps:
            step_dict = {
                "id": step.id,
                "task_id": step.task_id,
                "name": step.name,
                "description": step.description,
                "status": step.status,
                "result": step.result,
                "created_at": step.created_at,
                "updated_at": step.updated_at,
            }
            steps_list.append(step_dict)

        return {
            "task": task_dict,
            "steps": steps_list,
        }

    async def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> bool:
        """
        Update task details.

        Args:
            task_id: Task identifier
            title: New title (optional)
            description: New description (optional)
            status: New status (optional)

        Returns:
            True if updated successfully, False if task not found
        """
        logger.debug("Updating task", task_id=task_id, title=title, status=status)

        # Validate status if provided
        if status and status not in ["open", "in_progress", "closed"]:
            msg = f"Invalid status: {status}"
            raise ValueError(msg)

        # Get current task
        task = await self._task_repo.get_by_id(task_id)
        if not task:
            return False

        # Update fields if provided
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status

        # Save updated task
        await self._task_repo.save(task)
        logger.debug("Task updated", task_id=task_id)
        return True
