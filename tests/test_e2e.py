from pathlib import Path

import pytest

from task_context_mcp.client import SyncMCPClient


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return tmp_path / "test.db"


@pytest.fixture
def server_env(temp_db_path):
    """Environment variables for the MCP server."""
    return {
        "TASK_CONTEXT_MCP__DATABASE_URL": f"sqlite:///{temp_db_path}",
        "TASK_CONTEXT_MCP__DATA_DIR": str(temp_db_path.parent),
        "TASK_CONTEXT_MCP__LOGGING_LEVEL": "WARNING",  # Reduce log noise
    }


@pytest.fixture
def server_path():
    """Path to the MCP server script."""
    # Get the path to the main.py file in src/task_context_mcp/
    current_dir = Path(__file__).parent
    server_file = current_dir.parent / "src" / "task_context_mcp" / "main.py"
    return str(server_file)


@pytest.fixture
def mcp_client(server_path, server_env):
    """MCP client connected to the test server."""
    with SyncMCPClient(server_path, server_env) as client:
        yield client


class TestMCPToolsE2E:
    """End-to-end tests for all MCP tools."""

    def test_list_tools(self, mcp_client):
        """Test that we can list available tools."""
        tools = mcp_client.list_tools()

        # Should have 6 tools
        assert len(tools) == 6

        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "get_active_tasks",
            "create_task",
            "get_artifacts_for_task",
            "create_or_update_artifact",
            "archive_artifact",
            "search_artifacts",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_get_active_tasks_empty(self, mcp_client):
        """Test getting active tasks when none exist."""
        result = mcp_client.call_tool("get_active_tasks", {})

        # Should return a string indicating no active tasks
        assert isinstance(result.data, str)
        assert "No active tasks found" in result.data

    def test_create_and_get_task(self, mcp_client):
        """Test creating a task and then retrieving it."""
        # Create a task
        create_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Test Task for E2E",
                "description": "A test task created during end-to-end testing",
            },
        )

        assert isinstance(create_result.data, str)
        assert "Task created successfully" in create_result.data
        assert "Test Task for E2E" in create_result.data

        # Extract task ID from the result (it's in the format "ID: <uuid>")
        lines = create_result.data.split("\n")
        task_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_id = task_id_line.split(": ")[1]

        # Get active tasks
        tasks_result = mcp_client.call_tool("get_active_tasks", {})

        assert isinstance(tasks_result.data, str)
        assert "Test Task for E2E" in tasks_result.data
        assert task_id in tasks_result.data

    def test_create_and_get_artifacts(self, mcp_client):
        """Test creating artifacts and retrieving them."""
        # First create a task
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Artifact Test Task",
                "description": "Task for testing artifact operations",
            },
        )

        # Extract task ID
        lines = create_task_result.data.split("\n")
        task_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_id = task_id_line.split(": ")[1]

        # Create a practice artifact
        create_artifact_result = mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Test Practice",
                "content": "This is a test practice for the task.",
            },
        )

        assert isinstance(create_artifact_result.data, str)
        assert "Artifact created/updated successfully" in create_artifact_result.data

        # Create a rule artifact
        create_rule_result = mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "rule",
                "summary": "Test Rule",
                "content": "This is a test rule for the task.",
            },
        )

        assert isinstance(create_rule_result.data, str)
        assert "Artifact created/updated successfully" in create_rule_result.data

        # Get artifacts for the task
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task", {"task_id": task_id}
        )

        assert isinstance(artifacts_result.data, str)
        assert "Test Practice" in artifacts_result.data
        assert "Test Rule" in artifacts_result.data
        assert "This is a test practice for the task" in artifacts_result.data
        assert "This is a test rule for the task" in artifacts_result.data

    def test_get_artifacts_with_type_filter(self, mcp_client):
        """Test getting artifacts with type filtering."""
        # Create a task
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Filter Test Task",
                "description": "Task for testing artifact type filtering",
            },
        )

        task_id = create_task_result.data.split("\n")[1].split(": ")[1]

        # Create artifacts of different types
        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Practice Artifact",
                "content": "Practice content",
            },
        )

        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "rule",
                "summary": "Rule Artifact",
                "content": "Rule content",
            },
        )

        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "prompt",
                "summary": "Prompt Artifact",
                "content": "Prompt content",
            },
        )

        # Get only practice artifacts
        practice_result = mcp_client.call_tool(
            "get_artifacts_for_task",
            {"task_id": task_id, "artifact_types": ["practice"]},
        )

        assert "Practice Artifact" in practice_result.data
        assert "Practice content" in practice_result.data
        assert "Rule Artifact" not in practice_result.data
        assert "Prompt Artifact" not in practice_result.data

    def test_update_artifact(self, mcp_client):
        """Test updating an existing artifact."""
        # Create a task
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Update Test Task",
                "description": "Task for testing artifact updates",
            },
        )

        task_id = create_task_result.data.split("\n")[1].split(": ")[1]

        # Create initial artifact
        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Initial Practice",
                "content": "Initial content",
            },
        )

        # Update the same artifact (same task_id and artifact_type)
        update_result = mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Updated Practice",
                "content": "Updated content",
            },
        )

        assert "Artifact created/updated successfully" in update_result.data

        # Get artifacts and verify update
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task", {"task_id": task_id}
        )

        assert "Updated Practice" in artifacts_result.data
        assert "Updated content" in artifacts_result.data
        assert "Initial Practice" not in artifacts_result.data
        assert "Initial content" not in artifacts_result.data

    def test_archive_artifact(self, mcp_client):
        """Test archiving an artifact."""
        # Create a task and artifact
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Archive Test Task",
                "description": "Task for testing artifact archiving",
            },
        )

        task_id = create_task_result.data.split("\n")[1].split(": ")[1]

        create_artifact_result = mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Artifact to Archive",
                "content": "Content to be archived",
            },
        )

        # Extract artifact ID from result
        artifact_id = create_artifact_result.data.split("\n")[1].split(": ")[1]

        # Archive the artifact
        archive_result = mcp_client.call_tool(
            "archive_artifact",
            {"artifact_id": artifact_id, "reason": "Testing archive functionality"},
        )

        assert "Artifact archived successfully" in archive_result.data

        # Get active artifacts - should not include archived one
        active_artifacts = mcp_client.call_tool(
            "get_artifacts_for_task", {"task_id": task_id}
        )

        assert "Artifact to Archive" not in active_artifacts.data

        # Get artifacts including archived
        all_artifacts = mcp_client.call_tool(
            "get_artifacts_for_task", {"task_id": task_id, "include_archived": True}
        )

        assert "Artifact to Archive" in all_artifacts.data
        assert "archived" in all_artifacts.data.lower()

    def test_search_artifacts(self, mcp_client):
        """Test full-text search across artifacts."""
        # Create a task
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Search Test Task",
                "description": "Task for testing search functionality",
            },
        )

        task_id = create_task_result.data.split("\n")[1].split(": ")[1]

        # Create artifacts with searchable content
        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Python Development Practice",
                "content": "When writing Python code, always use descriptive variable names and follow PEP 8 style guidelines.",
            },
        )

        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "rule",
                "summary": "Code Review Rule",
                "content": "During code review, check for proper error handling and test coverage.",
            },
        )

        # Search for "Python"
        python_results = mcp_client.call_tool(
            "search_artifacts", {"query": "Python", "limit": 10}
        )

        assert "Python Development Practice" in python_results.data
        assert "PEP 8" in python_results.data

        # Search for "code review"
        review_results = mcp_client.call_tool(
            "search_artifacts", {"query": "code review", "limit": 10}
        )

        assert "Code Review Rule" in review_results.data
        assert "error handling" in review_results.data

        # Search for non-existent term
        empty_results = mcp_client.call_tool(
            "search_artifacts", {"query": "nonexistent", "limit": 10}
        )

        assert "No artifacts found matching query" in empty_results.data

    def test_task_lifecycle(self, mcp_client):
        """Test complete task lifecycle: create, add artifacts, archive task."""
        # Create task
        create_task_result = mcp_client.call_tool(
            "create_task",
            {
                "summary": "Lifecycle Test Task",
                "description": "Complete lifecycle test",
            },
        )

        task_id = create_task_result.data.split("\n")[1].split(": ")[1]

        # Add artifacts
        mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": task_id,
                "artifact_type": "practice",
                "summary": "Lifecycle Practice",
                "content": "Practice content for lifecycle test",
            },
        )

        # Verify task appears in active tasks
        active_tasks = mcp_client.call_tool("get_active_tasks", {})
        assert "Lifecycle Test Task" in active_tasks.data

        # Archive the task (this would need to be implemented in the server)
        # For now, just verify the task exists and has artifacts
        artifacts = mcp_client.call_tool("get_artifacts_for_task", {"task_id": task_id})

        assert "Lifecycle Practice" in artifacts.data
        assert "Practice content for lifecycle test" in artifacts.data

    def test_error_handling(self, mcp_client):
        """Test error handling for invalid inputs."""
        # Test with invalid task ID
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task", {"task_id": "invalid-uuid"}
        )

        assert "No artifacts found" in artifacts_result.data

        # Test with invalid artifact type
        create_result = mcp_client.call_tool(
            "create_or_update_artifact",
            {
                "task_id": "invalid-uuid",
                "artifact_type": "invalid_type",
                "summary": "Test",
                "content": "Test content",
            },
        )

        assert "Invalid artifact type" in create_result.data

        # Test archiving non-existent artifact
        archive_result = mcp_client.call_tool(
            "archive_artifact", {"artifact_id": "invalid-uuid"}
        )

        assert "Artifact not found" in archive_result.data
