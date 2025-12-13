from typing import Annotated, List, Optional

from pydantic import Field

from task_context_mcp.database import db_manager
from task_context_mcp.database.models import ArtifactStatus, ArtifactType
from task_context_mcp.server import mcp


# MCP Tools
@mcp.tool
def get_active_task_contexts() -> str:
    """
    ⚠️ MANDATORY FIRST STEP: ALWAYS call BEFORE ANY task. ⚠️
    Returns active task contexts (reusable task TYPES, not instances).
    Required to check for existing practices/rules/learnings.
    """
    try:
        task_contexts = db_manager.get_active_task_contexts()

        if not task_contexts:
            return """No active task contexts found.

⚠️ NEXT REQUIRED STEP: Since no existing task context matches your work,
you MUST call create_task_context() to create a new task type before proceeding.
Do NOT start task work without creating a context and adding initial artifacts."""

        result = "Active Task Contexts:\n\n"
        for tc in task_contexts:
            result += f"ID: {tc.id}\n"
            result += f"Summary: {tc.summary}\n"
            result += f"Description: {tc.description}\n"
            result += f"Created: {tc.creation_date}\n"
            result += f"Updated: {tc.updated_date}\n"
            result += "---\n"

        result += (
            "\n⚠️ NEXT REQUIRED STEP: If any context above matches your task type,\n"
        )
        result += "call get_artifacts_for_task_context(task_context_id) to load ALL artifacts\n"
        result += "BEFORE starting work. If no match found, create a new context with create_task_context()."

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
    ⚠️ REQUIRED when no match found. Create new task type (category, not instance).
    Example: "CV analysis for Python dev" NOT "Analyze John's CV"
    After creating: MUST call create_artifact() before starting work.
    """
    try:
        task_context = db_manager.create_task_context(
            summary=summary, description=description
        )

        return f"""Task context created successfully:
ID: {task_context.id}
Summary: {task_context.summary}
Description: {task_context.description}

⚠️ NEXT REQUIRED STEP: Now call create_artifact() to add initial practices, rules,
or prompts to this task context BEFORE starting any task work. Do not proceed without artifacts."""

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
    ⚠️ REQUIRED after find/create context. Load ALL artifacts BEFORE work.
    Call multiple times: at start, before major phases, when referencing patterns.
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
            return f"""No artifacts found for task context {task_context_id}{status_msg}.

⚠️ ACTION REQUIRED: This task context has no artifacts yet.
You MUST call create_artifact() to add initial practices, rules, or prompts
before starting task work. Do not proceed without establishing guidelines."""

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

        result += "\n✅ Artifacts loaded successfully. Now use these to guide your task execution.\n"
        result += "Remember to call create_artifact() during work when you discover new patterns/learnings."

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
    ⚠️ Call IMMEDIATELY when discovering patterns/learnings. Create DURING work, not at end.
    Types: practice (guidelines), rule (constraints), prompt (templates), result (learnings).
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

        return f"""Artifact created successfully:
ID: {artifact.id}
Type: {artifact.artifact_type}
Summary: {artifact.summary}

✅ Artifact saved. Continue creating artifacts as you discover more patterns/learnings during task execution."""

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
    Update artifact based on feedback/learnings. Use during work when refining understanding.
    Provide summary and/or content.
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
    Archive outdated/problematic artifacts. Use when no longer effective or superseded.
    Best practice: Create replacement first, then archive old. Provide reason.
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
    FTS5 search across artifacts. Find similar learnings/practices before creating new.
    Returns results ranked by relevance.
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
