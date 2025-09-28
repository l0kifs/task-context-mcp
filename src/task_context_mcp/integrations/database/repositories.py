"""Database repositories implementing business interfaces."""

from datetime import UTC, datetime

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from task_context_mcp.business.interfaces import StepRepository, TaskRepository
from task_context_mcp.config.logging_config import get_logger
from task_context_mcp.integrations.database.models import StepORM, TaskORM
from task_context_mcp.models.entities import (
    Step,
    Task,
)
from task_context_mcp.models.value_objects import (
    PaginationInfo,
    TaskListFilter,
    TaskListResult,
)

logger = get_logger(__name__)


class TaskRepositoryImpl(TaskRepository):
    """
    SQLAlchemy implementation of TaskRepository.

    Provides data access operations for Task entities using async SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self._session = session

    async def save(self, task: Task) -> Task:
        """
        Save a task to the database.

        Args:
            task: Task entity to save

        Returns:
            Saved task with assigned ID
        """
        logger.debug("Saving task", title=task.title)

        if task.id is not None:
            # Update existing task
            stmt = select(TaskORM).where(TaskORM.id == task.id)
            result = await self._session.execute(stmt)
            task_orm = result.scalar_one_or_none()

            if task_orm:
                # Update existing object
                task_orm.title = task.title
                task_orm.description = task.description
                task_orm.project_name = task.project_name
                task_orm.status = task.status
                task_orm.updated_at = task.updated_at
            else:
                # Task not found, this shouldn't happen
                msg = f"Task with ID {task.id} not found for update"
                raise ValueError(msg)
        else:
            # Create new task
            task_orm = TaskORM(
                title=task.title,
                description=task.description,
                project_name=task.project_name,
                status=task.status,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            self._session.add(task_orm)

        await self._session.commit()
        await self._session.refresh(task_orm)

        # Convert back to domain entity
        saved_task = Task(
            id=task_orm.id,
            title=task_orm.title,
            description=task_orm.description,
            project_name=task_orm.project_name,
            status=task_orm.status,
            created_at=task_orm.created_at,
            updated_at=task_orm.updated_at,
        )

        logger.debug("Task saved", task_id=saved_task.id)
        return saved_task

    async def get_by_id(self, task_id: int) -> Task | None:
        """
        Get a task by its ID.

        Args:
            task_id: Task identifier

        Returns:
            Task entity if found, None otherwise
        """
        logger.debug("Getting task by ID", task_id=task_id)

        stmt = select(TaskORM).where(TaskORM.id == task_id)
        result = await self._session.execute(stmt)
        task_orm = result.scalar_one_or_none()

        if not task_orm:
            return None

        return Task(
            id=task_orm.id,
            title=task_orm.title,
            description=task_orm.description,
            project_name=task_orm.project_name,
            status=task_orm.status,
            created_at=task_orm.created_at,
            updated_at=task_orm.updated_at,
        )

    async def get_by_id_with_steps(self, task_id: int) -> Task | None:
        """
        Get a task by ID with all its steps loaded.

        Args:
            task_id: Task identifier

        Returns:
            Task entity with steps if found, None otherwise
        """
        logger.debug("Getting task with steps", task_id=task_id)

        stmt = (
            select(TaskORM)
            .options(selectinload(TaskORM.steps))
            .where(TaskORM.id == task_id)
        )
        result = await self._session.execute(stmt)
        task_orm = result.scalar_one_or_none()

        if not task_orm:
            return None

        # Convert to domain entity with steps
        task = Task(
            id=task_orm.id,
            title=task_orm.title,
            description=task_orm.description,
            project_name=task_orm.project_name,
            status=task_orm.status,
            created_at=task_orm.created_at,
            updated_at=task_orm.updated_at,
        )

        # Add steps to task
        steps = []
        for step_orm in task_orm.steps:
            step = Step(
                id=step_orm.id,
                task_id=step_orm.task_id,
                name=step_orm.name,
                description=step_orm.description,
                status=step_orm.status,
                result=step_orm.result,
                created_at=step_orm.created_at,
                updated_at=step_orm.updated_at,
            )
            steps.append(step)

        task.steps = steps
        return task

    async def list_tasks(
        self, filter_criteria: TaskListFilter, page: int = 1, page_size: int = 10
    ) -> TaskListResult:
        """
        List tasks with filtering and pagination.

        Args:
            filter_criteria: Filtering and sorting criteria
            page: Page number (1-based)
            page_size: Number of tasks per page

        Returns:
            TaskListResult with tasks and pagination info
        """
        logger.debug(
            "Listing tasks",
            page=page,
            page_size=page_size,
            filter=filter_criteria.status_filter,
        )

        # Build base query
        query = select(TaskORM)

        # Apply status filter
        if filter_criteria.status_filter:
            query = query.where(TaskORM.status == filter_criteria.status_filter)

        # Get total count
        count_query = select(func.count(TaskORM.id))
        if filter_criteria.status_filter:
            count_query = count_query.where(
                TaskORM.status == filter_criteria.status_filter
            )

        total_count_result = await self._session.execute(count_query)
        total_count = total_count_result.scalar()

        # Apply sorting
        sort_column = getattr(TaskORM, filter_criteria.sort_by)
        if filter_criteria.sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self._session.execute(query)
        task_orms = result.scalars().all()

        # Convert to domain entities
        tasks = []
        for task_orm in task_orms:
            task = Task(
                id=task_orm.id,
                title=task_orm.title,
                description=task_orm.description,
                project_name=task_orm.project_name,
                status=task_orm.status,
                created_at=task_orm.created_at,
                updated_at=task_orm.updated_at,
            )
            tasks.append(task.model_dump())

        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return TaskListResult(tasks=tasks, pagination=pagination)

    async def update_status(self, task_id: int, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status value

        Returns:
            True if updated, False if task not found
        """
        logger.debug("Updating task status", task_id=task_id, status=status)

        now = datetime.now(UTC)

        # Update task status and updated_at
        stmt = select(TaskORM).where(TaskORM.id == task_id)
        result = await self._session.execute(stmt)
        task_orm = result.scalar_one_or_none()

        if not task_orm:
            return False

        task_orm.status = status
        task_orm.updated_at = now

        await self._session.commit()
        logger.debug("Task status updated", task_id=task_id, status=status)
        return True

    async def delete(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if task not found
        """
        logger.debug("Deleting task", task_id=task_id)

        stmt = select(TaskORM).where(TaskORM.id == task_id)
        result = await self._session.execute(stmt)
        task_orm = result.scalar_one_or_none()

        if not task_orm:
            return False

        await self._session.delete(task_orm)
        await self._session.commit()

        logger.debug("Task deleted", task_id=task_id)
        return True


class StepRepositoryImpl(StepRepository):
    """
    SQLAlchemy implementation of StepRepository.

    Provides data access operations for Step entities.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self._session = session

    async def save(self, step: Step) -> Step:
        """
        Save a task step to the database.

        Args:
            step: Step entity to save

        Returns:
            Saved task step with assigned ID
        """
        logger.debug("Saving task step", step_id=step.id, task_id=step.task_id)

        if step.id is not None:
            # Update existing step
            stmt = select(StepORM).where(StepORM.id == step.id)
            result = await self._session.execute(stmt)
            step_orm = result.scalar_one_or_none()

            if step_orm:
                # Update existing object
                step_orm.task_id = step.task_id
                step_orm.name = step.name
                step_orm.description = step.description
                step_orm.status = step.status
                step_orm.result = step.result
                step_orm.updated_at = step.updated_at
            else:
                # Step not found, this shouldn't happen
                msg = f"Task step with ID {step.id} not found for update"
                raise ValueError(msg)
        else:
            # Create new step
            step_orm = StepORM(
                task_id=step.task_id,
                name=step.name,
                description=step.description,
                status=step.status,
                result=step.result,
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            self._session.add(step_orm)

        await self._session.commit()
        await self._session.refresh(step_orm)

        # Convert back to domain entity
        saved_step = Step(
            id=step_orm.id,
            task_id=step_orm.task_id,
            name=step_orm.name,
            description=step_orm.description,
            status=step_orm.status,
            result=step_orm.result,
            created_at=step_orm.created_at,
            updated_at=step_orm.updated_at,
        )

        logger.debug("Task step saved", step_id=saved_step.id)
        return saved_step

    async def get_by_id(self, step_id: int) -> Step | None:
        """
        Get a step by its ID.

        Args:
            step_id: Step identifier

        Returns:
            Step entity if found, None otherwise
        """
        logger.debug("Getting step by ID", step_id=step_id)

        stmt = select(StepORM).where(StepORM.id == step_id)
        result = await self._session.execute(stmt)
        step_orm = result.scalar_one_or_none()

        if not step_orm:
            return None

        return Step(
            id=step_orm.id,
            task_id=step_orm.task_id,
            name=step_orm.name,
            description=step_orm.description,
            status=step_orm.status,
            result=step_orm.result,
            created_at=step_orm.created_at,
            updated_at=step_orm.updated_at,
        )

    async def get_by_task_id(self, task_id: int) -> list[Step]:
        """
        Get all steps for a task, ordered by creation time.

        Args:
            task_id: Task identifier

        Returns:
            List of Step entities ordered by creation time
        """
        logger.debug("Getting all steps for task", task_id=task_id)

        stmt = (
            select(StepORM)
            .where(StepORM.task_id == task_id)
            .order_by(StepORM.created_at)
        )

        result = await self._session.execute(stmt)
        step_orms = result.scalars().all()

        steps = []
        for step_orm in step_orms:
            step = Step(
                id=step_orm.id,
                task_id=step_orm.task_id,
                name=step_orm.name,
                description=step_orm.description,
                status=step_orm.status,
                result=step_orm.result,
                created_at=step_orm.created_at,
                updated_at=step_orm.updated_at,
            )
            steps.append(step)

        logger.debug("Steps retrieved", task_id=task_id, count=len(steps))
        return steps

    async def update_status(
        self, step_id: int, status: str, result: str | None = None
    ) -> bool:
        """
        Update step status and optionally result.

        Args:
            step_id: Step identifier
            status: New status value
            result: Optional result text

        Returns:
            True if updated, False if step not found
        """
        logger.debug("Updating step status", step_id=step_id, status=status)

        now = datetime.now(UTC)

        # Update step status, result and updated_at
        stmt = select(StepORM).where(StepORM.id == step_id)
        result_stmt = await self._session.execute(stmt)
        step_orm = result_stmt.scalar_one_or_none()

        if not step_orm:
            return False

        step_orm.status = status
        if result is not None:
            step_orm.result = result
        step_orm.updated_at = now

        await self._session.commit()
        logger.debug("Step status updated", step_id=step_id, status=status)
        return True

    async def delete(self, step_id: int) -> bool:
        """
        Delete a step.

        Args:
            step_id: Step identifier

        Returns:
            True if deleted, False if step not found
        """
        logger.debug("Deleting step", step_id=step_id)

        stmt = select(StepORM).where(StepORM.id == step_id)
        result = await self._session.execute(stmt)
        step_orm = result.scalar_one_or_none()

        if not step_orm:
            return False

        await self._session.delete(step_orm)
        await self._session.commit()

        logger.debug("Step deleted", step_id=step_id)
        return True

    async def save_batch(self, steps: list[Step]) -> list[Step]:
        """
        Save multiple steps to the database.

        Args:
            steps: List of Step entities to save

        Returns:
            List of saved steps with assigned IDs
        """
        logger.debug("Saving batch of steps", count=len(steps))

        # Convert domain entities to ORM models
        step_orms = []
        for step in steps:
            step_orm = StepORM(
                id=step.id,
                task_id=step.task_id,
                name=step.name,
                description=step.description,
                status=step.status,
                result=step.result,
                created_at=step.created_at,
                updated_at=step.updated_at,
            )
            step_orms.append(step_orm)

        self._session.add_all(step_orms)
        await self._session.commit()

        # Refresh all ORM objects to get IDs
        for step_orm in step_orms:
            await self._session.refresh(step_orm)

        # Convert back to domain entities
        saved_steps = []
        for step_orm in step_orms:
            saved_step = Step(
                id=step_orm.id,
                task_id=step_orm.task_id,
                name=step_orm.name,
                description=step_orm.description,
                status=step_orm.status,
                result=step_orm.result,
                created_at=step_orm.created_at,
                updated_at=step_orm.updated_at,
            )
            saved_steps.append(saved_step)

        logger.debug("Steps batch saved", count=len(saved_steps))
        return saved_steps

    async def update_batch(self, task_id: int, updates: list[dict]) -> bool:
        """
        Update multiple steps for a task.

        Args:
            task_id: Task identifier
            updates: List of update dicts with 'step_name', 'status',
            'description', 'updated_at'

        Returns:
            True if all updates successful
        """
        logger.debug(
            "Updating batch of steps", task_id=task_id, updates_count=len(updates)
        )

        for update_data in updates:
            step_name = update_data["step_name"]
            status = update_data["status"]
            description = update_data.get("description")
            updated_at = update_data["updated_at"]

            # Find step by name and task_id
            stmt = select(StepORM).where(
                StepORM.task_id == task_id, StepORM.name == step_name
            )
            result = await self._session.execute(stmt)
            step_orm = result.scalar_one_or_none()

            if step_orm:
                step_orm.status = status
                if description is not None:
                    step_orm.description = description
                step_orm.updated_at = updated_at

        await self._session.commit()
        logger.debug("Steps batch updated", task_id=task_id, updates_count=len(updates))
        return True
