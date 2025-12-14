from fastmcp import FastMCP

mcp = FastMCP(
    name="Task Context MCP Server",
    instructions="""
    ⚠️ MANDATORY WORKFLOW - ALL TASKS - NO EXCEPTIONS ⚠️
    
    REQUIRED WORKFLOW:
    1. ALWAYS START: Call get_active_task_contexts() BEFORE any work
    2. LOAD CONTEXT:
       - Match found? → get_artifacts_for_task_context(id) → Review artifacts → Start work
       - No match? → create_task_context() → create_artifact() → Start work
    3. DURING WORK: Call create_artifact() immediately when discovering patterns/learnings
    4. AFTER FEEDBACK: Call update_artifact() or archive_artifact() based on learnings
    5. BEFORE FINISHING: Call reflect_and_update_artifacts() to review learnings and manage artifacts
    
    VERIFY COMPLIANCE:
    ✅ First call is get_active_task_contexts()
    ✅ Artifacts loaded before work
    ✅ New artifacts created during (not after) work
    ✅ reflect_and_update_artifacts() called before finishing
    
    DO NOT:
    ❌ Skip step 1 or start without artifacts
    ❌ Wait until end to create artifacts
    ❌ Ignore loaded artifacts
    ❌ Treat this workflow as optional
    ❌ Say "task finished" without calling reflect_and_update_artifacts()
    
    ABOUT THIS SERVER:
    Manages task contexts (reusable task TYPES) and artifacts (practices, rules, prompts, learnings).
    Example task context: "CV analysis for Python developer" (NOT individual CV instances).
    Storage: SQLite + FTS5 for full-text search across historical learnings.
    
    TOOLS:
    - get_active_task_contexts: Check existing task types (ALWAYS CALL FIRST)
    - create_task_context: Create new task type when no match found
    - get_artifacts_for_task_context: Load practices/rules/prompts (BEFORE starting work)
    - create_artifact: Add learnings (IMMEDIATELY when discovered, not at end)
    - update_artifact: Refine existing artifacts based on feedback
    - archive_artifact: Mark outdated/incorrect artifacts (provide reason)
    - search_artifacts: FTS5 full-text search across all artifacts
    - reflect_and_update_artifacts: Review learnings and get prompted to update artifacts (BEFORE finishing)
    
    ARTIFACT TYPES:
    - practice: Best practices/guidelines for task execution
    - rule: Specific rules/constraints to follow
    - prompt: Template prompts useful for the task type
    - result: General patterns/learnings from past work (NOT individual results)
    
    CONTENT REQUIREMENTS:
    Language & Length:
    - Language: English only (Latin characters, 10% tolerance for code/technical terms)
    - Summary: max 200 characters
    - Description: max 1000 characters (task contexts only)
    - Artifact content: max 4000 characters (~500-700 words)
    
    Quality Guidelines - Store GENERALIZABLE patterns:
    ✅ DO STORE:
    - "Check import statements before running Python scripts"
    - "Always validate user input for SQL injection vulnerabilities"
    - "Use error handling pattern: try-except with specific exceptions"
    - Template prompts and reusable patterns
    
    ❌ DON'T STORE:
    - "Fixed bug in iteration 3" (iteration-specific)
    - "John updated this on 2024-03-15" (personal names/dates)
    - "Changed line 42 in user_service.py" (one-off solutions)
    - "/home/user/project/file.py" (project-specific paths)
    
    Focus on WHAT & WHY, not HOW (specifics):
    - Good: "Always validate API responses before processing to prevent null reference errors"
    - Bad: "Fixed the bug where response.data was null in the getUserProfile function"
    
    BEST PRACTICES:
    - Specific summaries: "CV analysis for Python/Django dev" not "Analyze CV"
    - Granular artifacts: Separate artifacts per aspect, not one massive file
    - Archive workflow: Create new → Archive old (with reason)
    - Search first: Check existing artifacts before creating duplicates
    - Immediate capture: Create artifacts when learning, not at task end
    - Concise content: Use bullet points, remove redundancy, break long content into multiple artifacts
    
    COMMON MISTAKES TO AVOID:
    ❌ "I'll check if needed" → Always check first
    ❌ "Add at end" → Capture immediately
    ❌ "Too simple for context" → All tasks use workflow
    ❌ "Just look, don't load" → Must load artifacts
    ❌ "I know better" → Artifacts contain validated learnings
    ❌ "Task finished" without reflection → Must call reflect_and_update_artifacts() first
    ❌ "Fixed mistakes" without updating artifacts → Create/update artifacts for each learning
    ❌ Storing iteration details → Store generalizable patterns only
    ❌ Non-English content → All content must be in English
    ❌ Exceeding length limits → Keep summaries <200, content <4000 chars
    
    DETAILED WORKFLOWS:
    
    New task type scenario:
    1. get_active_task_contexts() → no match found
    2. create_task_context(summary, description) → create the reusable task type
    3. create_artifact() → add initial practices/rules before starting
    4. get_artifacts_for_task_context() → load artifacts to review
    5. Execute work, calling create_artifact() as you discover patterns
    6. reflect_and_update_artifacts() → review learnings before finishing
    7. Handle feedback with update_artifact()/archive_artifact() as needed
    
    Existing task type scenario:
    1. get_active_task_contexts() → match found
    2. get_artifacts_for_task_context(id) → load ALL artifacts
    3. Review artifacts carefully before starting work
    4. Execute work using artifacts, create new ones as you learn
    5. reflect_and_update_artifacts() → review learnings before finishing
    6. Handle feedback with update_artifact()/archive_artifact() as needed
    """,
)
