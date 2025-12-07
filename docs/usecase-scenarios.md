# Usecase Scenarios

## Scenario 1: Working on new task
1. User asks agent to help with a task.
2. Agent analyses task context, provided by user.
3. Agent uses task-context-mcp to get a list of existing active tasks.
4. Agent analyse the list and finds no matching task.
5. Agent creates a new task in task-context-mcp.
6. Agent adds relevant artifacts (practices, rules, prompts) to the new task if available.
7. Agent implements the task using the artifacts and provides output to user.
8. User reviews the output and provides feedback.
9. Agent analyses feedback and updates artifacts in task-context-mcp if necessary. Agent can create new artifacts or archive artifacts based on feedback. 
10. Agent refines the task implementation based on updated artifacts and provides revised output to user.
11. User reviews the output and provides feedback.
12. Agent repeats steps 9-11 until user is satisfied with the output.

## Scenario 2: Continuing work on existing task
1. User asks agent to help with a task.
2. Agent analyses task context, provided by user.
3. Agent uses task-context-mcp to get a list of existing active tasks.
4. Agent analyses the list and finds a matching task.
5. Agent retrieves all relevant active artifacts for the existing task.
6. Agent implements the task using the artifacts and provides output to user.
7. User reviews the output and provides feedback.
8. Agent analyses feedback and updates artifacts in task-context-mcp if necessary. Agent can create new artifacts or archive artifacts based on feedback. 
9. Agent refines the task implementation based on updated artifacts and provides revised output to user.
10. User reviews the output and provides feedback.
11. Agent repeats steps 8-10 until user is satisfied with the output.
