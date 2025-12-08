from fastmcp import FastMCP


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
