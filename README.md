# Task Context MCP Server

An MCP (Model Context Protocol) server for managing task contexts and artifacts to enable AI agents to autonomously manage and improve execution processes for repetitive tasks.

## Overview

This MCP server provides a SQLite-based storage system that enables AI agents to:

- **Store and retrieve task contexts** with associated artifacts (practices, rules, prompts, results)
- **Perform full-text search** across historical results and best practices using SQLite FTS5
- **Manage artifact lifecycles** with active/archived status tracking
- **Enable autonomous process improvement** with minimal user intervention

## Features

### Core Functionality
- **Task Management**: Create, update, archive, and retrieve tasks
- **Artifact Storage**: Store practices, rules, prompts, and results for each task
- **Full-Text Search**: Efficient search across all artifacts using SQLite FTS5
- **Lifecycle Management**: Track active vs archived artifacts with reasons
- **Transaction Safety**: ACID compliance for all database operations

### MCP Tools Available

1. **`get_active_tasks`** - Get all currently active tasks
2. **`create_task`** - Create a new task with summary and description
3. **`get_artifacts_for_task`** - Retrieve all artifacts for a specific task
4. **`create_or_update_artifact`** - Create new or update existing artifacts
5. **`archive_artifact`** - Archive artifacts with optional reason
6. **`search_artifacts`** - Full-text search across all artifacts

## Installation

### Prerequisites
- Python 3.12+
- uv package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/l0kifs/task-context-mcp.git
cd task-context-mcp

# Install dependencies
uv sync

# Run tests
uv run pytest
```

## Usage

### Running the MCP Server

```bash
# Run as a module
uv run python -m task_context_mcp.main

# Or directly
uv run python src/task_context_mcp/main.py
```

### MCP Client Configuration

#### For Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "task-context": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/task-context-mcp", "python", "-m", "task_context_mcp.main"]
    }
  }
}
```

#### For VS Code/Cursor
Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "task-context": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/task-context-mcp", "python", "-m", "task_context_mcp.main"]
    }
  }
}
```

### MCP Tools Available

The server provides the following tools via MCP:

#### 1. `get_active_tasks`
Get all active tasks in the system with their metadata.
- **Returns**: List of active tasks with id, summary, description, creation/update dates

#### 2. `create_task`
Create a new task with summary and description.
- **Parameters**: 
  - `summary` (string): Brief task description
  - `description` (string): Detailed task description
- **Returns**: Created task information

#### 3. `get_artifacts_for_task`
Retrieve all active artifacts for a specific task.
- **Parameters**:
  - `task_id` (string): ID of the task
  - `artifact_types` (optional list): Types to retrieve ('practice', 'rule', 'prompt', 'result')
  - `include_archived` (boolean): Whether to include archived artifacts
- **Returns**: All matching artifacts with content

#### 4. `create_or_update_artifact`
Create a new artifact or update an existing one for a task.
- **Parameters**:
  - `task_id` (string): Associated task ID
  - `artifact_type` (string): Type ('practice', 'rule', 'prompt', 'result')
  - `summary` (string): Brief description
  - `content` (string): Full artifact content
- **Returns**: Created/updated artifact information

#### 5. `archive_artifact`
Archive an artifact, marking it as no longer active.
- **Parameters**:
  - `artifact_id` (string): ID of artifact to archive
  - `reason` (optional string): Reason for archiving
- **Returns**: Archived artifact information

#### 6. `search_artifacts`
Perform full-text search across all artifacts.
- **Parameters**:
  - `query` (string): Search query
  - `limit` (integer): Maximum results (default: 10)
- **Returns**: Matching artifacts ranked by relevance

## Architecture

### Database Schema

- **tasks**: Task definitions with metadata and status tracking
- **artifacts**: Artifact storage with lifecycle management
- **artifacts_fts**: FTS5 virtual table for full-text search indexing

### Key Components

- `src/task_context_mcp/main.py`: MCP server implementation with FastMCP
- `src/task_context_mcp/database/models.py`: SQLAlchemy ORM models
- `src/task_context_mcp/database/database.py`: Database operations and FTS5 management
- `src/task_context_mcp/config/`: Configuration management with Pydantic settings

### Technology Stack

- **Database**: SQLite 3.35+ with FTS5 extension
- **ORM**: SQLAlchemy 2.0+ for type-safe database operations
- **MCP Framework**: FastMCP for Model Context Protocol implementation
- **Configuration**: Pydantic Settings for environment-based config
- **Logging**: Loguru for structured, multi-level logging
- **Development**: UV for Python package and dependency management

### Business Requirements Alignment

This implementation fulfills all requirements from `docs/BRD.md`:

- ✅ **Task Catalog**: UUID-based task identification with metadata
- ✅ **Artifact Storage**: Lifecycle management with active/archived status
- ✅ **Full-Text Search**: FTS5-based search with BM25 ranking
- ✅ **Context Loading**: Automatic retrieval based on task matching
- ✅ **Autonomous Updates**: Agent-driven improvements with feedback loops
- ✅ **ACID Compliance**: Transaction-based operations with SQLite
- ✅ **Minimal Query Processing**: Support for natural language task matching

## Use Case Scenarios

### Scenario 1: Working on a New Task
1. **User Request**: "Help me write requirements for a new user authentication feature"
2. **Agent Analysis**: Agent analyzes the request and identifies it as a requirements writing task
3. **Task Discovery**: Agent calls `get_active_tasks` to check for existing similar tasks
4. **Task Creation**: No matching task found, so agent calls `create_task` with:
   - Summary: "User Authentication Requirements"
   - Description: "Write detailed requirements for user authentication feature"
5. **Context Loading**: Agent calls `get_artifacts_for_task` to load any existing artifacts
6. **Task Execution**: Agent uses loaded artifacts (practices, rules, prompts) to write requirements
7. **Artifact Updates**: Based on execution results, agent calls `create_or_update_artifact` to store successful approaches

### Scenario 2: Continuing Existing Work
1. **User Request**: "Continue working on the CV analysis feature we discussed last week"
2. **Task Matching**: Agent calls `get_active_tasks` and finds matching task by summary/description
3. **Context Retrieval**: Agent calls `get_artifacts_for_task` with the task ID to load all relevant artifacts
4. **Continued Execution**: Agent uses the loaded context (practices, rules, prompts, previous results) to continue work
5. **Process Improvement**: Agent refines artifacts based on current execution and user feedback

### Scenario 3: Finding Similar Past Work
1. **User Request**: "Help me optimize this database query"
2. **Search for Inspiration**: Agent calls `search_artifacts` with keywords like "database optimization" or "query performance"
3. **Review Results**: Agent examines returned artifacts for similar past approaches
4. **Adapt Patterns**: Agent adapts successful patterns from historical artifacts to current task
5. **Store New Artifacts**: Agent creates new artifacts documenting the current successful approach

### Scenario 4: Autonomous Process Improvement
1. **Task Completion**: Agent completes a task and receives user feedback
2. **Success Analysis**: Agent analyzes whether the execution was successful
3. **Artifact Updates**: 
   - Successful approaches: `create_or_update_artifact` to store improved practices/rules
   - Outdated methods: `archive_artifact` with reason for archival
4. **Future Benefit**: Subsequent tasks automatically benefit from the improved artifacts

## Configuration

The server uses the following configuration (via environment variables or `.env` file):

- `TASK_CONTEXT_MCP__DATA_DIR`: Data directory path (default: `./data`)
- `TASK_CONTEXT_MCP__DATABASE_URL`: Database URL (default: `sqlite:///./data/task_context.db`)
- `TASK_CONTEXT_MCP__LOGGING_LEVEL`: Logging level (default: `INFO`)

## Data Model

### Tasks
- **id**: Unique UUID identifier
- **summary**: Brief task description for matching
- **description**: Detailed task description
- **creation_date**: When task was created
- **updated_date**: When task was last modified
- **status**: 'active' or 'archived'

### Artifacts
- **id**: Unique UUID identifier
- **task_id**: Reference to associated task
- **artifact_type**: 'practice', 'rule', 'prompt', or 'result'
- **summary**: Brief artifact description
- **content**: Full artifact content
- **status**: 'active' or 'archived'
- **archived_at**: Timestamp when archived (if applicable)
- **archivation_reason**: Reason for archiving
- **created_at**: When artifact was created

## Development

### Running Tests
```bash
uv run pytest
```

### Code Quality
```bash
# Lint and format
uv run ruff check
uv run ruff format

# Type checking
uv run ty
```

## License

MIT License - see LICENSE file for details.</content>
<parameter name="filePath">/home/serj/dev/my-github-repos/task-context-mcp/README.md
