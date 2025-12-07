"""
Task Context MCP Server

An MCP server for managing task contexts and artifacts to enable AI agents
to autonomously manage and improve execution processes for repetitive tasks.
"""

from typing import List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config.logging import setup_logging
from .database.database import db_manager
from .database.models import ArtifactStatus, ArtifactType

# Initialize logging
setup_logging()

# Initialize database
db_manager.init_db()

# Create MCP server
mcp = FastMCP(
    name="Task Context MCP Server",
    instructions="""
    This MCP server manages task contexts and artifacts for AI agents.
    Use the available tools to:
    - Get active tasks to understand what tasks are available
    - Create new tasks when working on something new
    - Retrieve artifacts (practices, rules, prompts, results) for tasks
    - Create or update artifacts based on execution results
    - Archive outdated artifacts
    - Search across all artifacts using full-text search

    The server uses SQLite with FTS5 for efficient full-text search across
    historical results and best practices.
    """,
)


# Pydantic models for tool parameters
class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""

    summary: str = Field(..., description="Summary of the task")
    description: str = Field(..., description="Detailed description of the task")


class ArtifactCreateRequest(BaseModel):
    """Request model for creating/updating an artifact."""

    task_id: str = Field(..., description="ID of the task this artifact belongs to")
    artifact_type: str = Field(
        ..., description="Type of artifact: 'practice', 'rule', 'prompt', 'result'"
    )
    summary: str = Field(..., description="Summary of the artifact")
    content: str = Field(..., description="Full content of the artifact")


class ArtifactArchiveRequest(BaseModel):
    """Request model for archiving an artifact."""

    artifact_id: str = Field(..., description="ID of the artifact to archive")
    reason: Optional[str] = Field(None, description="Reason for archiving the artifact")


class GetArtifactsRequest(BaseModel):
    """Request model for getting artifacts for a task."""

    task_id: str = Field(..., description="ID of the task")
    artifact_types: Optional[List[str]] = Field(
        None, description="Types of artifacts to retrieve"
    )
    include_archived: bool = Field(
        False, description="Whether to include archived artifacts"
    )


class SearchArtifactsRequest(BaseModel):
    """Request model for searching artifacts."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum number of results to return")


# MCP Tools
@mcp.tool
def get_active_tasks() -> str:
    """
    Get all active tasks in the system.

    Returns a list of active tasks with their metadata (id, summary, description, creation_date, updated_date).
    This is useful for agents to understand what tasks are currently available and find matching tasks
    for their current work.
    """
    try:
        tasks = db_manager.get_active_tasks()

        if not tasks:
            return "No active tasks found."

        result = "Active Tasks:\n\n"
        for task in tasks:
            result += f"ID: {task.id}\n"
            result += f"Summary: {task.summary}\n"
            result += f"Description: {task.description}\n"
            result += f"Created: {task.creation_date}\n"
            result += f"Updated: {task.updated_date}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error getting active tasks: {str(e)}"


@mcp.tool
def create_task(summary: str, description: str) -> str:
    """
    Create a new task in the system.

    Use this when an agent is working on a task that doesn't exist yet in the system.
    The agent should analyze the task context and create a new task if no matching
    active task is found.

    Args:
        summary: Summary of the task
        description: Detailed description of the task
    """
    try:
        task = db_manager.create_task(summary=summary, description=description)

        return f"Task created successfully:\nID: {task.id}\nSummary: {task.summary}\nDescription: {task.description}"

    except Exception as e:
        return f"Error creating task: {str(e)}"


@mcp.tool
def get_artifacts_for_task(
    task_id: str,
    artifact_types: Optional[List[str]] = None,
    include_archived: bool = False,
) -> str:
    """
    Get all active artifacts for a specific task.

    This automatically loads relevant context (practices, rules, prompts, results)
    for a task. Use this when continuing work on an existing task or when
    an agent needs to retrieve all relevant artifacts for task execution.

    Args:
        task_id: ID of the task
        artifact_types: Types of artifacts to retrieve (optional)
        include_archived: Whether to include archived artifacts (default: False)
    """
    try:
        # Convert string types to ArtifactType enums
        artifact_type_enums = None
        if artifact_types:
            try:
                artifact_type_enums = [ArtifactType(t) for t in artifact_types]
            except ValueError as e:
                return f"Invalid artifact type: {str(e)}. Must be one of: {[t.value for t in ArtifactType]}"

        status = None if include_archived else ArtifactStatus.ACTIVE

        artifacts = db_manager.get_artifacts_for_task(
            task_id=task_id, artifact_types=artifact_type_enums, status=status
        )

        if not artifacts:
            status_msg = " (including archived)" if include_archived else ""
            return f"No artifacts found for task {task_id}{status_msg}."

        result = f"Artifacts for task {task_id}:\n\n"
        for artifact in artifacts:
            result += f"ID: {artifact.id}\n"
            result += f"Type: {artifact.artifact_type}\n"
            result += f"Summary: {artifact.summary}\n"
            result += f"Content:\n{artifact.content}\n"
            result += f"Status: {artifact.status}\n"
            if artifact.archived_at:
                result += f"Archived At: {artifact.archived_at}\n"
                result += f"Archive Reason: {artifact.archivation_reason}\n"
            result += f"Created: {artifact.created_at}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error getting artifacts for task: {str(e)}"


@mcp.tool
def create_or_update_artifact(
    task_id: str, artifact_type: str, summary: str, content: str
) -> str:
    """
    Create a new artifact or update an existing one for a task.

    Use this during task execution to:
    - Add new practices, rules, prompts, or results
    - Update existing artifacts based on execution feedback
    - Improve workflows autonomously based on success/failure analysis

    If an artifact of the same type already exists for the task, it will be updated.
    Otherwise, a new artifact will be created.

    Args:
        task_id: ID of the task this artifact belongs to
        artifact_type: Type of artifact: 'practice', 'rule', 'prompt', 'result'
        summary: Summary of the artifact
        content: Full content of the artifact
    """
    try:
        # Validate artifact_type
        if artifact_type not in [t.value for t in ArtifactType]:
            return f"Invalid artifact type: {artifact_type}. Must be one of: {[t.value for t in ArtifactType]}"

        artifact = db_manager.create_artifact(
            task_id=task_id,
            artifact_type=ArtifactType(artifact_type),
            summary=summary,
            content=content,
        )

        return f"Artifact created/updated successfully:\nID: {artifact.id}\nType: {artifact.artifact_type}\nSummary: {artifact.summary}"

    except Exception as e:
        return f"Error creating/updating artifact: {str(e)}"


@mcp.tool
def archive_artifact(artifact_id: str, reason: Optional[str] = None) -> str:
    """
    Archive an artifact, marking it as no longer active.

    Use this when:
    - An artifact is no longer relevant or has been superseded
    - User feedback indicates an artifact should be replaced
    - Agent analysis shows an artifact is causing failures

    Archived artifacts are excluded from active context loading but remain
    available for historical queries.

    Args:
        artifact_id: ID of the artifact to archive
        reason: Reason for archiving the artifact (optional)
    """
    try:
        artifact = db_manager.archive_artifact(artifact_id=artifact_id, reason=reason)

        if artifact:
            reason_msg = f" (Reason: {reason})" if reason else ""
            return f"Artifact archived successfully:\nID: {artifact.id}\nReason: {artifact.archivation_reason}{reason_msg}"
        else:
            return f"Artifact not found: {artifact_id}"

    except Exception as e:
        return f"Error archiving artifact: {str(e)}"


@mcp.tool
def search_artifacts(query: str, limit: int = 10) -> str:
    """
    Search across all artifacts using full-text search.

    This enables finding similar past results, practices, or rules.
    Useful for:
    - Finding relevant context for new tasks
    - Discovering similar approaches from past work
    - Getting inspiration from historical artifacts

    Returns results ranked by relevance score.

    Args:
        query: Search query
        limit: Maximum number of results to return (default: 10)
    """
    try:
        results = db_manager.search_artifacts(query=query, limit=limit)

        if not results:
            return f"No artifacts found matching query: '{query}'"

        result = f"Search results for '{query}' (limit: {limit}):\n\n"
        for row in results:
            artifact_id, summary, content, task_id, rank = row
            result += f"Artifact ID: {artifact_id}\n"
            result += f"Task ID: {task_id}\n"
            result += f"Summary: {summary}\n"
            result += f"Content Preview: {content[:200]}{'...' if len(content) > 200 else ''}\n"
            result += f"Relevance Rank: {rank}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error searching artifacts: {str(e)}"


if __name__ == "__main__":
    mcp.run()
