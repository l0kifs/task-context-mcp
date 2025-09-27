"""Database repositories implementing business interfaces."""

from datetime import UTC

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from task_context_mcp.business.interfaces import TaskRepository, TaskSummaryRepository
from task_context_mcp.config.logging_config import get_logger
from task_context_mcp.integrations.database.models import TaskORM, TaskSummaryORM
from task_context_mcp.models.entities import (
    Task,
    TaskSummary,
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

        # Convert domain entity to ORM model
        task_orm = TaskORM(
            id=task.id,
            title=task.title,
            description=task.description,
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
            status=task_orm.status,
            created_at=task_orm.created_at,
            updated_at=task_orm.updated_at,
        )

    async def get_by_id_with_summaries(self, task_id: int) -> Task | None:
        """
        Get a task by ID with all its summaries loaded.

        Args:
            task_id: Task identifier

        Returns:
            Task entity with summaries if found, None otherwise
        """
        logger.debug("Getting task with summaries", task_id=task_id)

        stmt = (
            select(TaskORM)
            .options(selectinload(TaskORM.summaries))
            .where(TaskORM.id == task_id)
        )
        result = await self._session.execute(stmt)
        task_orm = result.scalar_one_or_none()

        if not task_orm:
            return None

        return Task(
            id=task_orm.id,
            title=task_orm.title,
            description=task_orm.description,
            status=task_orm.status,
            created_at=task_orm.created_at,
            updated_at=task_orm.updated_at,
        )

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

        from datetime import datetime

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


class TaskSummaryRepositoryImpl(TaskSummaryRepository):
    """
    SQLAlchemy implementation of TaskSummaryRepository.

    Provides data access operations for TaskSummary entities.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self._session = session

    async def save(self, summary: TaskSummary) -> TaskSummary:
        """
        Save a task summary to the database.

        Args:
            summary: TaskSummary entity to save

        Returns:
            Saved summary with assigned ID
        """
        logger.debug(
            "Saving task summary", task_id=summary.task_id, step=summary.step_number
        )

        # Convert domain entity to ORM model
        summary_orm = TaskSummaryORM(
            id=summary.id,
            task_id=summary.task_id,
            step_number=summary.step_number,
            summary=summary.summary,
            created_at=summary.created_at,
        )

        # Use merge to handle both insert and update
        summary_orm = await self._session.merge(summary_orm)
        await self._session.commit()
        await self._session.refresh(summary_orm)

        # Convert back to domain entity
        saved_summary = TaskSummary(
            id=summary_orm.id,
            task_id=summary_orm.task_id,
            step_number=summary_orm.step_number,
            summary=summary_orm.summary,
            created_at=summary_orm.created_at,
        )

        logger.debug("Task summary saved", summary_id=saved_summary.id)
        return saved_summary

    async def get_by_task_and_step(
        self, task_id: int, step_number: int
    ) -> TaskSummary | None:
        """
        Get a summary by task ID and step number.

        Args:
            task_id: Task identifier
            step_number: Step number

        Returns:
            TaskSummary if found, None otherwise
        """
        logger.debug(
            "Getting summary by task and step", task_id=task_id, step=step_number
        )

        stmt = select(TaskSummaryORM).where(
            TaskSummaryORM.task_id == task_id, TaskSummaryORM.step_number == step_number
        )
        result = await self._session.execute(stmt)
        summary_orm = result.scalar_one_or_none()

        if not summary_orm:
            return None

        return TaskSummary(
            id=summary_orm.id,
            task_id=summary_orm.task_id,
            step_number=summary_orm.step_number,
            summary=summary_orm.summary,
            created_at=summary_orm.created_at,
        )

    async def get_all_by_task_id(self, task_id: int) -> list[TaskSummary]:
        """
        Get all summaries for a task, ordered by step number.

        Args:
            task_id: Task identifier

        Returns:
            List of TaskSummary entities ordered by step number
        """
        logger.debug("Getting all summaries for task", task_id=task_id)

        stmt = (
            select(TaskSummaryORM)
            .where(TaskSummaryORM.task_id == task_id)
            .order_by(TaskSummaryORM.step_number)
        )

        result = await self._session.execute(stmt)
        summary_orms = result.scalars().all()

        summaries = []
        for summary_orm in summary_orms:
            summary = TaskSummary(
                id=summary_orm.id,
                task_id=summary_orm.task_id,
                step_number=summary_orm.step_number,
                summary=summary_orm.summary,
                created_at=summary_orm.created_at,
            )
            summaries.append(summary)

        logger.debug("Summaries retrieved", task_id=task_id, count=len(summaries))
        return summaries
