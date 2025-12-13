from fastmcp import FastMCP

mcp = FastMCP(
    name="Task Context MCP Server",
    instructions="""
    ⚠️ MANDATORY WORKFLOW - ALL TASKS - NO EXCEPTIONS ⚠️
    
    1. ALWAYS call get_active_task_contexts() FIRST (before any work)
    2. Match found? → get_artifacts_for_task_context() → review → start work
       No match? → create_task_context() → create_artifact() → start work
    3. During work: create_artifact() immediately when discovering patterns
    4. After feedback: update_artifact() or archive_artifact()
    
    DO NOT: Skip step 1, start without artifacts, wait to create artifacts, ignore artifacts, treat as optional.
    
    ABOUT THIS SERVER:
    Manages task contexts (reusable task TYPES) and artifacts (practices, rules, prompts, learnings).
    Example task context: "CV analysis for Python developer" (NOT individual CV instances).
    
    TOOLS:
    - get_active_task_contexts: Check existing task types (CALL FIRST)
    - create_task_context: Create new task type when no match found
    - get_artifacts_for_task_context: Load practices/rules/prompts (BEFORE work)
    - create_artifact: Add learnings (IMMEDIATELY when discovered, not at end)
    - update_artifact: Refine based on feedback
    - archive_artifact: Mark outdated artifacts
    - search_artifacts: FTS5 search across artifacts
    
    ARTIFACT TYPES:
    - practice: Best practices/guidelines
    - rule: Specific rules/constraints
    - prompt: Template prompts
    - result: General patterns/learnings (NOT individual results)
    
    WORKFLOWS:
    
    New task type:
    1. get_active_task_contexts() → no match
    2. create_task_context(summary, description)
    3. create_artifact() for initial practices/rules
    4. get_artifacts_for_task_context() before work
    5. Do work, create_artifact() as you learn
    6. Handle feedback with update_artifact()/archive_artifact()
    
    Existing task type:
    1. get_active_task_contexts() → match found
    2. get_artifacts_for_task_context(id)
    3. Review artifacts before work
    4. Do work using artifacts, create new ones as you learn
    5. Handle feedback with update_artifact()/archive_artifact()
    
    SQLite + FTS5 for storage and full-text search.
    """,
)
