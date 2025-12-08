"""
Task Context MCP Server

An MCP server for managing task contexts and artifacts to enable AI agents
to autonomously manage and improve execution processes for repetitive task types.

Task contexts represent reusable task categories (e.g., "CV analysis for Python developers"),
not individual task instances. Artifacts store general practices, rules, prompts, and
learnings that can be applied to any instance of that task type.
"""

from typing import Annotated, List, Optional

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
    
    IMPORTANT: Task contexts represent reusable TASK TYPES, not individual task instances.
    For example, "Analyze applicant CV for Python developer" is a task context.
    Individual CV analyses are NOT stored - only reusable artifacts that help with this type of work.
    
    CRITICAL: Active Use Throughout Task Execution
    
    Task contexts and artifacts are NOT just for setup and completion - they must be 
    ACTIVELY USED throughout the entire task execution:
    
    - Retrieve artifacts BEFORE starting analysis/work, not just when creating context
    - Reference artifacts DURING work to guide your approach and decisions
    - Create NEW artifacts as you discover patterns, learnings, or effective approaches
    - Update artifacts when you refine understanding, not just at the end
    - Use artifacts to structure your output and ensure completeness
    
    Common mistake: Creating a task context at the start, then forgetting to use it.
    Always retrieve and apply artifacts throughout task execution.
    
    MAIN USE CASE SCENARIOS:
    
    Scenario 1 - Working on a NEW Task Type:
    1. User asks you to help with a task (e.g., "analyze this CV for Python developer position")
    2. Use get_active_task_contexts() to get list of existing task contexts
    3. Analyze the list - if NO matching task context exists:
       a. Create a new task context using create_task_context()
       b. Add relevant artifacts (practices, rules, prompts) if you have knowledge to share
    4. BEFORE implementing: Retrieve artifacts using get_artifacts_for_task_context()
       to ensure you follow established practices and rules
    5. DURING implementation: 
       a. Reference artifacts to guide your work
       b. Create new artifacts (create_artifact) as you discover effective patterns
       c. Update artifacts (update_artifact) if you refine approaches
    6. Implement the task using artifacts and provide output to user
    7. Based on user feedback, update artifacts (create new or archive existing)
    8. Repeat refinement until user is satisfied
    
    Scenario 2 - Continuing Work on EXISTING Task Type:
    1. User asks you to help with a task (e.g., "analyze another CV for Python developer")
    2. Use get_active_task_contexts() to get list of existing task contexts
    3. Analyze the list - if a MATCHING task context exists:
       a. Use get_artifacts_for_task_context() to load all relevant artifacts
       b. Apply the loaded practices, rules, and prompts to your work
    4. DURING implementation:
       a. Continuously reference the loaded artifacts to guide your work
       b. Create new artifacts (create_artifact) as you discover new patterns or learnings
       c. Update artifacts (update_artifact) if approaches need refinement
    5. Implement the task using the artifacts and provide output to user
    6. Based on user feedback, update artifacts (create new or archive existing)
    7. Repeat refinement until user is satisfied
    
    AVAILABLE TOOLS:
    - get_active_task_contexts: Find matching task types for your current work
    - create_task_context: Create new task context when working on a new type of task
    - get_artifacts_for_task_context: Load practices, rules, prompts, learnings for 
      a task context. Call this MULTIPLE TIMES during task execution - at the start,
      before major work phases, and when you need to reference established patterns.
    - create_artifact: Add new practices, rules, prompts, or learnings. Use this 
      IMMEDIATELY when you discover something useful during task execution, not just
      at the end. Create artifacts as you learn, not as an afterthought.
    - update_artifact: Refine existing artifacts based on feedback
    - archive_artifact: Mark outdated artifacts as archived
    - search_artifacts: Full-text search across all artifacts

    WORKFLOW CHECKLIST - Use this to ensure proper task context usage:
    
    □ At task start: Check for existing task context (get_active_task_contexts)
    □ If context exists: Load artifacts (get_artifacts_for_task_context)
    □ If no context: Create one (create_task_context) and initial artifacts
    □ Before major work steps: Review relevant artifacts
    □ During work: Reference artifacts to guide decisions and structure
    □ As you learn: Create new artifacts (create_artifact) immediately
    □ When refining: Update artifacts (update_artifact) with improvements
    □ Before completion: Ensure all learnings are captured as artifacts
    
    Remember: Artifacts are living knowledge - create and update them throughout
    task execution, not just at the beginning or end.
    
    ARTIFACT TYPES:
    - practice: Best practices and guidelines for executing the task type
    - rule: Specific rules and constraints to follow
    - prompt: Template prompts useful for the task type
    - result: General patterns and learnings from past work (NOT individual execution results)
    
    The server uses SQLite with FTS5 for efficient full-text search.
    """,
)


# Pydantic models for tool parameters
class TaskContextCreateRequest(BaseModel):
    """Request model for creating a new task context."""

    summary: str = Field(..., description="Summary of the task context (task type)")
    description: str = Field(
        ..., description="Detailed description of the task context"
    )


class ArtifactCreateRequest(BaseModel):
    """Request model for creating an artifact."""

    task_context_id: str = Field(
        ..., description="ID of the task context this artifact belongs to"
    )
    artifact_type: str = Field(
        ..., description="Type of artifact: 'practice', 'rule', 'prompt', 'result'"
    )
    summary: str = Field(..., description="Summary of the artifact")
    content: str = Field(..., description="Full content of the artifact")


class ArtifactUpdateRequest(BaseModel):
    """Request model for updating an artifact."""

    artifact_id: str = Field(..., description="ID of the artifact to update")
    summary: Optional[str] = Field(None, description="New summary for the artifact")
    content: Optional[str] = Field(None, description="New content for the artifact")


class ArtifactArchiveRequest(BaseModel):
    """Request model for archiving an artifact."""

    artifact_id: str = Field(..., description="ID of the artifact to archive")
    reason: Optional[str] = Field(None, description="Reason for archiving the artifact")


class GetArtifactsRequest(BaseModel):
    """Request model for getting artifacts for a task context."""

    task_context_id: str = Field(..., description="ID of the task context")
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
def get_active_task_contexts() -> str:
    """
    Get all active task contexts in the system.

    Returns a list of active task contexts with their metadata.
    Task contexts represent reusable TASK TYPES (e.g., "CV analysis for Python developer"),
    not individual task instances.

    Use this to find if a matching task context already exists for your current work.
    """
    try:
        task_contexts = db_manager.get_active_task_contexts()

        if not task_contexts:
            return "No active task contexts found."

        result = "Active Task Contexts:\n\n"
        for tc in task_contexts:
            result += f"ID: {tc.id}\n"
            result += f"Summary: {tc.summary}\n"
            result += f"Description: {tc.description}\n"
            result += f"Created: {tc.creation_date}\n"
            result += f"Updated: {tc.updated_date}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error getting active task contexts: {str(e)}"


@mcp.tool
def create_task_context(
    summary: Annotated[
        str, Field(description="Summary of the task context (task type)")
    ],
    description: Annotated[
        str, Field(description="Detailed description of the task context")
    ],
) -> str:
    """
    Create a new task context (reusable task type).

    Use this when working on a type of task that doesn't exist yet in the system.
    Task contexts represent categories of work, not individual instances.

    Example: "Analyze applicant CV for Python developer of specific stack"
    NOT: "Analyze John's CV" (individual instance)
    """
    try:
        task_context = db_manager.create_task_context(
            summary=summary, description=description
        )

        return f"Task context created successfully:\nID: {task_context.id}\nSummary: {task_context.summary}\nDescription: {task_context.description}"

    except Exception as e:
        return f"Error creating task context: {str(e)}"


@mcp.tool
def get_artifacts_for_task_context(
    task_context_id: Annotated[str, Field(description="ID of the task context")],
    artifact_types: Annotated[
        Optional[List[str]],
        Field(description="Types of artifacts to retrieve (optional, defaults to all)"),
    ] = None,
    include_archived: Annotated[
        bool, Field(description="Whether to include archived artifacts")
    ] = False,
) -> str:
    """
    Get all artifacts for a specific task context.

    This loads relevant context (practices, rules, prompts, learnings) for a task type.
    Use this when working on a task to retrieve all relevant artifacts.
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

        artifacts = db_manager.get_artifacts_for_task_context(
            task_context_id=task_context_id,
            artifact_types=artifact_type_enums,
            status=status,
        )

        if not artifacts:
            status_msg = " (including archived)" if include_archived else ""
            return f"No artifacts found for task context {task_context_id}{status_msg}."

        result = f"Artifacts for task context {task_context_id}:\n\n"
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
        return f"Error getting artifacts for task context: {str(e)}"


@mcp.tool
def create_artifact(
    task_context_id: Annotated[
        str, Field(description="ID of the task context this artifact belongs to")
    ],
    artifact_type: Annotated[
        str,
        Field(description="Type of artifact: 'practice', 'rule', 'prompt', 'result'"),
    ],
    summary: Annotated[str, Field(description="Summary of the artifact")],
    content: Annotated[str, Field(description="Full content of the artifact")],
) -> str:
    """
    Create a new artifact for a task context.

    Multiple artifacts of the same type can exist per task context.
    Use this to add new practices, rules, prompts, or learnings.

    Artifact types:
    - practice: Best practices and guidelines
    - rule: Specific rules and constraints
    - prompt: Template prompts
    - result: General patterns/learnings from past work (NOT individual results)
    """
    try:
        # Validate artifact_type
        if artifact_type not in [t.value for t in ArtifactType]:
            return f"Invalid artifact type: {artifact_type}. Must be one of: {[t.value for t in ArtifactType]}"

        artifact = db_manager.create_artifact(
            task_context_id=task_context_id,
            artifact_type=ArtifactType(artifact_type),
            summary=summary,
            content=content,
        )

        return f"Artifact created successfully:\nID: {artifact.id}\nType: {artifact.artifact_type}\nSummary: {artifact.summary}"

    except Exception as e:
        return f"Error creating artifact: {str(e)}"


@mcp.tool
def update_artifact(
    artifact_id: Annotated[str, Field(description="ID of the artifact to update")],
    summary: Annotated[
        Optional[str], Field(description="New summary for the artifact")
    ] = None,
    content: Annotated[
        Optional[str], Field(description="New content for the artifact")
    ] = None,
) -> str:
    """
    Update an existing artifact's summary and/or content.

    Use this to refine artifacts based on feedback or new learnings.
    At least one of summary or content must be provided.
    """
    try:
        if summary is None and content is None:
            return "Error: At least one of 'summary' or 'content' must be provided."

        artifact = db_manager.update_artifact(
            artifact_id=artifact_id, summary=summary, content=content
        )

        if artifact:
            return f"Artifact updated successfully:\nID: {artifact.id}\nSummary: {artifact.summary}"
        else:
            return f"Artifact not found: {artifact_id}"

    except Exception as e:
        return f"Error updating artifact: {str(e)}"


@mcp.tool
def archive_artifact(
    artifact_id: Annotated[str, Field(description="ID of the artifact to archive")],
    reason: Annotated[
        Optional[str],
        Field(description="Reason for archiving the artifact (recommended)"),
    ] = None,
) -> str:
    """
    Archive an artifact, marking it as no longer active.

    Use this when:
    - An artifact is no longer relevant or has been superseded
    - User feedback indicates an artifact should be replaced
    - Analysis shows an artifact is causing issues

    Archived artifacts are excluded from active context loading but remain
    available for historical queries.
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
def search_artifacts(
    query: Annotated[str, Field(description="Search query")],
    limit: Annotated[
        int, Field(description="Maximum number of results to return")
    ] = 10,
) -> str:
    """
    Search across all artifacts using full-text search.

    This enables finding similar past learnings, practices, or rules.
    Useful for:
    - Finding relevant context for new task contexts
    - Discovering similar approaches from past work
    - Getting inspiration from historical artifacts

    Returns results ranked by relevance score.
    """
    try:
        if not query or not query.strip():
            return "Error: Search query cannot be empty."

        results = db_manager.search_artifacts(query=query, limit=limit)

        if not results:
            return f"No artifacts found matching query: '{query}'"

        result = f"Search results for '{query}' (limit: {limit}):\n\n"
        for row in results:
            artifact_id, summary, content, task_context_id, rank = row
            result += f"Artifact ID: {artifact_id}\n"
            result += f"Task Context ID: {task_context_id}\n"
            result += f"Summary: {summary}\n"
            result += f"Content Preview: {content[:200]}{'...' if len(content) > 200 else ''}\n"
            result += f"Relevance Rank: {rank}\n"
            result += "---\n"

        return result

    except Exception as e:
        return f"Error searching artifacts: {str(e)}"


def run():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
