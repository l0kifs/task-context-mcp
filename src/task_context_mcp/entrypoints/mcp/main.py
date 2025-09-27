"""MCP server entrypoint for Task Context MCP."""

import asyncio
from typing import Any

from fastmcp import FastMCP

from task_context_mcp.business.services import TaskService
from task_context_mcp.config.logging_config import setup_logging
from task_context_mcp.integrations.database.manager import DatabaseManager
from task_context_mcp.integrations.database.repositories import (
    TaskRepositoryImpl,
    TaskSummaryRepositoryImpl,
)

# Global variables for dependency injection
db_manager: DatabaseManager | None = None
task_service: TaskService | None = None


async def initialize_dependencies() -> None:
    """Initialize all dependencies for the MCP server."""
    global db_manager, task_service

    # Set up logging
    setup_logging()

    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.initialize()

    # Create repositories
    session = db_manager.get_session()
    task_repo = TaskRepositoryImpl(session)
    summary_repo = TaskSummaryRepositoryImpl(session)

    # Create services
    task_service = TaskService(task_repo, summary_repo)


# Initialize MCP server
mcp = FastMCP(name="Task Context Server")


@mcp.tool()
async def create_task(title: str, description: str | None = None) -> dict[str, Any]:
    """
    Creates a new task and returns its ID.

    This function allows an AI agent to create new tasks for tracking
    work progress and preserving context between sessions.

    Args:
        title: Task title (required, 1-255 characters)
        description: Task description (optional, up to 1000 characters)

    Returns:
        Dict with the operation result:
            - success: True on successful creation
            - task_id: ID of the created task
            - message: Description of the result
            - error: Error description (only when success=False)
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        task_id = await task_service.create_task(title=title, description=description)

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task '{title}' created with ID {task_id}",
        }
    except ValueError as e:
        return {"success": False, "error": f"Validation error: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Error creating task: {e!s}"}


@mcp.tool()
async def save_summary(task_id: int, step_number: int, summary: str) -> dict[str, Any]:
    """
    Saves a summary for a task step.

    Allows an agent to save step-by-step progress for later
    context restoration. If a summary for the step already exists, it will be updated.

    Args:
        task_id: Task ID (required, positive integer)
        step_number: Step number (required, positive integer)
        summary: Summary text (required, 1-5000 characters)

    Returns:
        Dict with the operation result:
            - success: True on successful save
            - message: Description of the result
            - error: Error description (only when success=False)
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        success = await task_service.save_summary(
            task_id=task_id,
            step_number=step_number,
            summary=summary,
        )

        if success:
            return {
                "success": True,
                "message": f"Summary for step {step_number} of task {task_id} saved",
            }
        return {"success": False, "error": f"Task with ID {task_id} not found"}
    except ValueError as e:
        return {"success": False, "error": f"Validation error: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Error saving summary: {e!s}"}


@mcp.tool()
async def get_task_context(task_id: int) -> dict[str, Any]:
    """
    Returns an optimized task context for restoration.

    Provides the agent with a compressed task context optimized to
    minimize token usage while preserving all necessary information.

    Args:
        task_id: Task ID (required, positive integer)

    Returns:
        Dict with the operation result:
            On success (success=True):
            - success: True when retrieval succeeds
            - context: Task context
                - task_id: Task ID
                - title: Task title
                - description: Task description
                - total_steps: Total number of steps
                - context_summary: Compressed summary of all steps
                - last_updated: Last updated time in ISO format
            On failure (success=False):
            - success: False on error
            - error: Error description
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        context = await task_service.get_task_context(task_id)

        if context:
            return {
                "success": True,
                "context": {
                    "task_id": context.task_id,
                    "title": context.title,
                    "description": context.description,
                    "total_steps": context.total_steps,
                    "context_summary": context.context_summary,
                    "last_updated": context.last_updated,
                },
            }
        return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        return {"success": False, "error": f"Error retrieving context: {e!s}"}


@mcp.tool()
async def list_tasks(
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """
    Returns a list of user tasks with filtering and pagination.

    Allows an agent to view existing tasks, filter them by status, and sort
    them for efficient workflow management.

    Args:
        status_filter: Status filter ("open", "completed", or None for all)
        page: Page number (default: 1)
        page_size: Page size (default: 10, max: 100)
        sort_by: Field to sort by ("created_at", "updated_at", "title")
        sort_order: Sort order ("asc", "desc")

    Returns:
        Dict with the operation result:
            On success (success=True):
            - success: True when retrieval succeeds
            - tasks: List of tasks with their attributes
            - pagination: Pagination metadata
                - page: Current page
                - page_size: Page size
                - total_count: Total number of tasks
                - total_pages: Total number of pages
                - has_next: Whether there is a next page
                - has_prev: Whether there is a previous page
            On failure (success=False):
            - success: False on error
            - error: Error description
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        result = await task_service.list_tasks(
            status_filter=status_filter,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Convert the result to a dictionary
        tasks_data = []
        for task in result.tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            tasks_data.append(task_dict)

        return {
            "success": True,
            "tasks": tasks_data,
            "pagination": {
                "page": result.pagination.page,
                "page_size": result.pagination.page_size,
                "total_count": result.pagination.total_count,
                "total_pages": result.pagination.total_pages,
                "has_next": result.pagination.has_next,
                "has_prev": result.pagination.has_prev,
            },
        }
    except Exception as e:
        return {"success": False, "error": f"Error retrieving task list: {e!s}"}


@mcp.tool()
async def update_task_status(task_id: int, status: str) -> dict[str, Any]:
    """
    Updates a task's status (open/completed).

    Allows an agent to change task statuses to reflect current
    work state.

    Args:
        task_id: Task ID (required, positive integer)
        status: New status ("open" or "completed")

    Returns:
        Dict with the operation result:
            On success (success=True):
            - success: True on successful update
            - message: Confirmation of status change
            On failure (success=False):
            - success: False on error
            - error: Error description
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        success = await task_service.update_task_status(task_id, status)

        if success:
            status_text = "completed" if status == "completed" else "open"
            return {
                "success": True,
                "message": f"Status of task {task_id} changed to '{status_text}'",
            }
        return {"success": False, "error": f"Task with ID {task_id} not found"}
    except ValueError as e:
        return {"success": False, "error": f"Validation error: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Error updating status: {e!s}"}


@mcp.tool()
async def delete_task(task_id: int) -> dict[str, Any]:
    """
    Deletes a task and all its summaries.

    Completely removes the task and all related data.
    This operation is irreversible.

    Args:
        task_id: ID of the task to delete (required, positive integer)

    Returns:
        Dict with the operation result:
            On success (success=True):
            - success: True on successful deletion
            - message: Deletion confirmation
            On failure (success=False):
            - success: False on error
            - error: Error description
    """
    if not task_service:
        return {"success": False, "error": "Service not initialized"}

    try:
        success = await task_service.delete_task(task_id)

        if success:
            return {"success": True, "message": f"Task {task_id} deleted"}
        return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        return {"success": False, "error": f"Error deleting task: {e!s}"}


async def main():
    """Main entry point for the MCP server."""
    try:
        # Initialize dependencies
        await initialize_dependencies()

        # Run MCP server
        await mcp.run_async()

    except Exception:
        # Log error and re-raise
        if db_manager:
            await db_manager.close()
        raise
    finally:
        # Ensure database connections are closed
        if db_manager:
            await db_manager.close()


def run():
    """Synchronous entry point for the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    # Run the server
    run()
