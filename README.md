
# Task Context MCP Server

MCP (Model Context Protocol) server for saving and restoring AI agent task context. Allows the agent to save a summary of each task step in the database and quickly restore context when switching to a new chat.

## Features

- ✅ Create and manage tasks
- ✅ Save summary for each task step
- ✅ Fast context restoration for tasks
- ✅ Summary optimization for token minimization
- ✅ Asynchronous work with SQLite database
- ✅ Full compatibility with MCP protocol
- ✅ Clean Architecture with dependency injection

## Installation

### Requirements

- Python 3.12+
- uv (package manager)

### Setup

```bash
git clone <repository-url>
cd task-context-mcp
uv sync
```

## Usage

### Start the server

```bash
uv run task-context-mcp
```

If you need to run the server while your current working directory is different from the project directory, use the `--project` option with the project path. This tells `uv` to run the command in the context of that project (it will discover the project's `pyproject.toml` and `.venv`):

```fish
uv run --project /home/serj/dev/my-github-repos/task-context-mcp task-context-mcp
```

The server will start and listen for MCP connections via stdio.

### MCP Tools

The server provides the following tools for AI agents:

#### `create_task(title, description=None)`
Creates a new task and returns its ID.

#### `save_summary(task_id, step_number, summary)`
Saves a summary for a task step.

#### `get_task_context(task_id)`
Returns optimized task context for restoration.

#### `list_tasks(status_filter=None, page=1, page_size=10, sort_by="updated_at", sort_order="desc")`
Returns a list of tasks with filtering and pagination.

#### `update_task_status(task_id, status)`
Updates task status ("open" or "completed").

#### `delete_task(task_id)`
Deletes a task and all its summaries.

### MCP Resources

#### `agent://workflow_rules`
Returns general rules for AI agent workflow with MCP tools.

#### `summary://compression_rules`
Returns summary optimization rules for the agent.

## Integration with AI Agents

### Claude Desktop

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "task-context": {
      "command": "uv",
      "args": ["run", "task-context-mcp"],
      "cwd": "/path/to/task-context-mcp"
    }
  }
}
```

### Cursor

Configure MCP server in Cursor settings, specifying the path to the executable file.

## Testing

```bash
uv run pytest
```

## License

MIT License
