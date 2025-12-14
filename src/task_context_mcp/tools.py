from typing import Annotated, List, Optional

from pydantic import Field

from task_context_mcp.database import db_manager
from task_context_mcp.database.models import ArtifactStatus, ArtifactType
from task_context_mcp.server import mcp

# Default artifact types to retrieve (excludes RESULT type)
DEFAULT_ARTIFACT_TYPES = [
    ArtifactType.PRACTICE,
    ArtifactType.RULE,
    ArtifactType.PROMPT,
]


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
        str,
        Field(
            description="Summary of the task context (task type) - max 200 chars, English only"
        ),
    ],
    description: Annotated[
        str,
        Field(
            description="Detailed description of the task context - max 1000 chars, English only"
        ),
    ],
) -> str:
    """
    ⚠️ REQUIRED when no match found. Create new task type (category, not instance).
    Example: "CV analysis for Python dev" NOT "Analyze John's CV"

    CONTENT REQUIREMENTS:
    - English only (Latin characters)
    - Summary: max 200 characters
    - Description: max 1000 characters
    - Focus on the TASK TYPE, not specific instances

    After creating: MUST call create_artifact() before starting work.
    """
    try:
        # Validation is handled by Pydantic models in the MCP layer
        task_context = db_manager.create_task_context(
            summary=summary, description=description
        )

        return f"""Task context created successfully:
ID: {task_context.id}
Summary: {task_context.summary}
Description: {task_context.description}

⚠️ NEXT REQUIRED STEP: Now call create_artifact() to add initial practices, rules,
or prompts to this task context BEFORE starting any task work. Do not proceed without artifacts.

⚠️ DURING TASK: You MUST autonomously manage artifacts:
• Create artifacts immediately when discovering patterns/mistakes/learnings
• Update artifacts when you find they're incomplete or incorrect
• Archive artifacts when they prove wrong or outdated
• Call reflect_and_update_artifacts() before finishing the task"""

    except Exception as e:
        return f"Error creating task context: {str(e)}"


@mcp.tool
def get_artifacts_for_task_context(
    task_context_id: Annotated[str, Field(description="ID of the task context")],
    artifact_types: Annotated[
        Optional[List[str]],
        Field(
            description="Types of artifacts to retrieve (optional, defaults to all except 'result')"
        ),
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
        # Default to all types except RESULT
        if artifact_types is None:
            artifact_type_enums = DEFAULT_ARTIFACT_TYPES
        else:
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

        result += "\n✅ Artifacts loaded successfully. Now use these to guide your task execution.\n\n"
        result += "⚠️ CRITICAL REMINDERS:\n"
        result += "• Call create_artifact() IMMEDIATELY when discovering patterns/learnings/mistakes\n"
        result += "• Call update_artifact() IMMEDIATELY when you find artifacts are incomplete/wrong\n"
        result += "• Call archive_artifact() IMMEDIATELY when artifacts prove incorrect/outdated\n"
        result += (
            "• Call reflect_and_update_artifacts() BEFORE saying task is finished\n"
        )
        result += "• DO NOT wait for user to ask - manage artifacts autonomously!\n"

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
    summary: Annotated[
        str,
        Field(description="Summary of the artifact - max 200 chars, English only"),
    ],
    content: Annotated[
        str,
        Field(
            description="Full content of the artifact - max 4000 chars, English only"
        ),
    ],
) -> str:
    """
    ⚠️ REQUIRED during task execution when discovering patterns/learnings/mistakes.
    Call IMMEDIATELY (not at task end) when you:
    - Discover a pattern or best practice
    - Learn something new about the task type
    - Find a mistake/correction that others should know about
    - Identify a rule or constraint

    CONTENT REQUIREMENTS:
    - English only (Latin characters)
    - Summary: max 200 characters
    - Content: max 4000 characters (≈500-700 words)
    - Store GENERALIZABLE patterns, not specific iteration details
    - Focus on WHAT and WHY, not specific names/dates/iteration numbers

    Types: practice (guidelines), rule (constraints), prompt (templates), result (learnings).
    """
    try:
        # Validate artifact_type
        if artifact_type not in [t.value for t in ArtifactType]:
            return f"Invalid artifact type: {artifact_type}. Must be one of: {[t.value for t in ArtifactType]}"

        # Validation for length and language is handled by Pydantic models in the MCP layer

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

✅ Artifact saved. Continue creating artifacts as you discover more patterns/learnings.
⚠️ Remember: Before finishing the task, call reflect_and_update_artifacts() to ensure all learnings are captured."""

    except Exception as e:
        return f"Error creating artifact: {str(e)}"


@mcp.tool
def update_artifact(
    artifact_id: Annotated[str, Field(description="ID of the artifact to update")],
    summary: Annotated[
        Optional[str],
        Field(description="New summary for the artifact - max 200 chars, English only"),
    ] = None,
    content: Annotated[
        Optional[str],
        Field(
            description="New content for the artifact - max 4000 chars, English only"
        ),
    ] = None,
) -> str:
    """
    ⚠️ REQUIRED when you discover an artifact needs improvement.
    Update artifact immediately when:
    - You find an existing practice/rule is incorrect or incomplete
    - User feedback indicates an artifact needs refinement
    - You learn something that improves an existing artifact

    CONTENT REQUIREMENTS:
    - English only (Latin characters)
    - Summary: max 200 characters
    - Content: max 4000 characters (≈500-700 words)
    - Store GENERALIZABLE patterns, not specific iteration details
    - Focus on WHAT and WHY, not specific names/dates/iteration numbers

    Use during work when refining understanding. Provide summary and/or content.
    """
    try:
        if summary is None and content is None:
            return "Error: At least one of 'summary' or 'content' must be provided."

        artifact = db_manager.update_artifact(
            artifact_id=artifact_id, summary=summary, content=content
        )

        if artifact:
            return f"""Artifact updated successfully:
ID: {artifact.id}
Summary: {artifact.summary}

✅ Update applied. Continue monitoring and updating artifacts as you discover more learnings.
⚠️ Remember: Before finishing the task, call reflect_and_update_artifacts() to review all changes."""
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
    ⚠️ REQUIRED when you discover an artifact is incorrect/outdated/problematic.
    Archive immediately when:
    - An artifact proves to be incorrect or misleading
    - A practice/rule is superseded by a better approach
    - User feedback indicates an artifact should no longer be used
    Best practice: Create replacement first, then archive old. Always provide reason.
    """
    try:
        artifact = db_manager.archive_artifact(artifact_id=artifact_id, reason=reason)

        if artifact:
            return f"""Artifact archived successfully:
ID: {artifact.id}
Reason: {artifact.archivation_reason}

✅ Artifact archived. If this was due to discovering it's incorrect, ensure you've created a replacement.
⚠️ Remember: Before finishing the task, call reflect_and_update_artifacts() to review all changes."""
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


@mcp.tool
def reflect_and_update_artifacts(
    task_context_id: Annotated[
        str, Field(description="ID of the task context used for this work")
    ],
    learnings: Annotated[
        str,
        Field(
            description="What you learned during task execution (mistakes found, corrections made, patterns discovered, etc.)"
        ),
    ],
) -> str:
    """
    ⚠️ MANDATORY after completing work or making corrections/mistakes.
    Call when:
    - Task is complete (before saying "finished")
    - You discovered mistakes and corrected them
    - You learned something important about the task type
    - User provided feedback that improved your approach

    This tool helps you reflect on learnings and prompts you to update artifacts.
    You MUST then call create_artifact/update_artifact/archive_artifact as needed.
    """
    try:
        # Get current artifacts for this task context (excluding result type)
        artifacts = db_manager.get_artifacts_for_task_context(
            task_context_id=task_context_id,
            artifact_types=DEFAULT_ARTIFACT_TYPES,
            status=ArtifactStatus.ACTIVE,
        )

        result = f"""📊 REFLECTION CHECKPOINT - Task Context: {task_context_id}

Your Learnings:
{learnings}

Current Active Artifacts ({len(artifacts)} total):
"""

        if artifacts:
            for artifact in artifacts:
                result += f"\n- [{artifact.artifact_type}] {artifact.summary} (ID: {artifact.id})"
        else:
            result += "\n⚠️ NO ARTIFACTS EXIST YET!"

        result += """

⚠️⚠️⚠️ REQUIRED ACTIONS - DO NOT SKIP ⚠️⚠️⚠️

Based on your learnings above, you MUST NOW:

1. ✅ CREATE new artifacts for NEW learnings/patterns/mistakes discovered
   → Call create_artifact() for each new practice, rule, or learning
   → Example: If you found imports issue, create a rule about checking imports

2. ✅ UPDATE existing artifacts that need improvement
   → Call update_artifact() if existing artifacts were incomplete or wrong
   → Use artifact IDs listed above

3. ✅ ARCHIVE artifacts that proved incorrect or outdated
   → Call archive_artifact() with clear reason for each obsolete artifact
   → Example: If a rule was wrong, archive it and create a corrected version

❌ DO NOT:
- Say "I'll update artifacts" without actually calling the tools
- Skip artifact management because "task is simple"
- Wait for user to ask you to update artifacts
- Finish the task without managing artifacts

⏭️ NEXT STEP: Call the appropriate artifact management tools NOW.
"""

        return result

    except Exception as e:
        return f"Error during reflection: {str(e)}"
