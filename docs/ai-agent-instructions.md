# AI Agent Rules for Working with Task Context MCP

## General Principles

### 1. Context Awareness
- **Always** check for active tasks before starting work
- Use `list_tasks` to get an overview of current tasks
- Restore context via `get_task_context` when switching to a new chat

### 2. Proactive Task Management
- Create a new task (`create_task`) for every significant project or request
- Do not create tasks for simple questions that need a single answer
- Group related activities within a single task

## When to Use Tools

### `create_task` - Creating a Task
**Use when:**
- The user starts a new project or a complex task
- The work will require multiple steps or sessions
- You need to track progress
- The task may be paused and resumed later

**Examples:**
- "Develop a web application"
- "Analyze sales data"
- "Create a marketing campaign plan"

**DO NOT use for:**
- Simple questions ("What is Python?")
- One-off requests
- Fixing code bugs

### `save_summary` - Saving Progress
**Use after each meaningful step:**
- Completion of a work stage
- Problem resolution
- Making an important decision
- Achieving an intermediate result

**Summary structure:**
```
Done: [short description]
Result: [what was achieved]
Problems: [if any]
Next: [next step]
```

**Save frequency:**
- After every 10-15 minutes of active work
- When the work direction changes
- Before moving to a new component/module
- When issues are discovered and resolved

### `get_task_context` - Restoring Context
**Use when:**
- The user returns to a paused task
- You need to recall what was done previously
- You must assess current progress
- You're planning the next steps

**After restoring:**
- Briefly summarize the current state
- Suggest options for continuation
- Clarify priorities with the user

### `list_tasks` - Task Overview
**Use for:**
- Showing active projects to the user
- Choosing a task to continue working on
- Assessing overall workload
- Planning priorities

**Filtering parameters:**
- `status_filter`: "open" (only active), "completed" (only finished), null (all)
- `page`, `page_size`: for paginating large lists
- `sort_by`: "updated_at" (by update), "created_at" (by creation), "title" (by name)
- `sort_order`: "desc" (newest first), "asc" (oldest first)

**Recommendations:**
- By default show only open tasks
- Use pagination for large numbers of tasks
- Sort by update time for recency

### `update_task_status` - Changing Task Status
**Use when:**
- The task is fully completed (status="completed")
- You need to reopen a completed task (status="open")
- The user explicitly requests a status change

**Statuses:**
- "open" - the task is active and work continues
- "completed" - the task is finished and the goal is reached

### `delete_task` - Deleting Tasks
**Use only when:**
- The user explicitly asks to delete the task
- The task is cancelled or no longer relevant
- The task was created by mistake

**ATTENTION:** This operation is irreversible! Prefer using `update_task_status` with "completed" instead of deleting.

## Working Strategies

### Session Start
1. Greet the user
2. Run `list_tasks` for an overview
3. If there are active tasks - offer to continue
4. If this is a new request - assess whether creating a task is necessary

### During Work
1. Save progress regularly with `save_summary`
2. Focus on outcomes, not process
3. Document important decisions and their rationale
4. Note problems and how they were resolved

### Session End
1. Save a final summary with results
2. Indicate the task status (completed/paused)
3. Describe next steps if the task isn't finished
4. Offer the user a plan for subsequent actions

## Performance Optimization

### Token Minimization
- Use concise summaries (up to 200 words)
- Avoid duplicating information
- Focus on key results
- Use technical terms without extra explanation

### Context Management
- Regularly "flush" old context via summaries
- Restore only the necessary information
- Group related steps into logical blocks

### Effective Planning
- Break large tasks into stages
- Set clear completion criteria for steps
- Plan checkpoints to evaluate progress

## Error Handling

### On Tool Failures
- Inform the user about the issue
- Propose alternative ways to continue
- Save current progress before retrying

### On Loss of Context
- Use `get_task_context` to restore
- Ask the user to clarify current goals
- Start with a brief summary of your understanding

## Examples of Good Practices

### ✅ Good:
- Creating a task "Develop API for an online store"
- Summary: "Done: Created DB models. Result: Ready models with relationships. Problems: none. Next: API endpoints"
- Restoring context before continuing work

### ❌ Bad:
- Creating a task for the question "How does HTTP work?"
- Summary: "I thought for a long time about how best to implement the function, then decided to use SQLAlchemy as the ORM, then created models for the tables tasks and task_summaries. In the Task model I added fields id, title, description, created_at, updated_at. In the TaskSummary model I added fields id, task_id, step_number, summary, created_at. Also configured relationships between tables."
- Working without saving progress

Remember: MCP tools are your "external memory". Use them to create a continuous, efficient experience for the user.

## Summary Optimization Rules for the AI Agent

### Goal
Create concise yet informative summaries for each task step to minimize tokens while preserving context quality.

### Compression Principles

1. **Focus on the outcome**: Describe what was achieved, not how.
2. **Key decisions**: Record important technical decisions and their rationale.
3. **Problems and resolutions**: Briefly note encountered problems and how they were solved.
4. **Next steps**: State what will be done next.

### Summary structure (recommended)
```
Done: [short description]
Result: [what was achieved]
Problems: [if any]
Next: [next step]
```

### Constraints
- Maximum 200 words per summary
- Avoid repeating information from previous steps
- Use technical terms without extra explanation
- Store only critically important information

### Examples

❌ Bad:
"I started working on creating the database. First I studied the requirements, then I chose SQLAlchemy as the ORM, then I created models for the tasks and task_summaries tables. In the Task model I added fields id, title, description, created_at, updated_at. In the TaskSummary model I added fields id, task_id, step_number, summary, created_at. I also configured relationships between the tables."

✅ Good:
"Done: Created DB models (Task, TaskSummary) with SQLAlchemy
Result: Ready models with relationships, async support
Problems: none
Next: Implement the service layer"