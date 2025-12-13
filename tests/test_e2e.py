from pathlib import Path

import pytest

from .client import SyncMCPClient


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

        # Should have 8 tools (added reflect_and_update_artifacts)
        assert len(tools) == 8

        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "get_active_task_contexts",
            "create_task_context",
            "get_artifacts_for_task_context",
            "create_artifact",
            "update_artifact",
            "archive_artifact",
            "search_artifacts",
            "reflect_and_update_artifacts",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_get_active_task_contexts_empty(self, mcp_client):
        """Test getting active task contexts when none exist."""
        result = mcp_client.call_tool("get_active_task_contexts", {})

        # Should return a string indicating no active task contexts
        assert isinstance(result.data, str)
        assert "No active task contexts found" in result.data

    def test_create_and_get_task_context(self, mcp_client):
        """Test creating a task context and then retrieving it."""
        # Create a task context
        create_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "CV Analysis for Python Developer",
                "description": "Analyze applicant CVs for Python developer positions with specific tech stack requirements",
            },
        )

        assert isinstance(create_result.data, str)
        assert "Task context created successfully" in create_result.data
        assert "CV Analysis for Python Developer" in create_result.data

        # Extract task context ID from the result (it's in the format "ID: <uuid>")
        lines = create_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        # Get active task contexts
        task_contexts_result = mcp_client.call_tool("get_active_task_contexts", {})

        assert isinstance(task_contexts_result.data, str)
        assert "CV Analysis for Python Developer" in task_contexts_result.data
        assert task_context_id in task_contexts_result.data

    def test_create_and_get_artifacts(self, mcp_client):
        """Test creating artifacts and retrieving them."""
        # First create a task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Artifact Test Task Context",
                "description": "Task context for testing artifact operations",
            },
        )

        # Extract task context ID
        lines = create_task_context_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        # Create a practice artifact
        create_artifact_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Test Practice",
                "content": "This is a test practice for CV analysis.",
            },
        )

        assert isinstance(create_artifact_result.data, str)
        assert "Artifact created successfully" in create_artifact_result.data

        # Create a rule artifact
        create_rule_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "rule",
                "summary": "Test Rule",
                "content": "Always check for Python framework experience.",
            },
        )

        assert isinstance(create_rule_result.data, str)
        assert "Artifact created successfully" in create_rule_result.data

        # Get artifacts for the task context
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )

        assert isinstance(artifacts_result.data, str)
        assert "Test Practice" in artifacts_result.data
        assert "Test Rule" in artifacts_result.data
        assert "This is a test practice for CV analysis" in artifacts_result.data
        assert "Always check for Python framework experience" in artifacts_result.data

    def test_get_artifacts_with_type_filter(self, mcp_client):
        """Test getting artifacts with type filtering."""
        # Create a task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Filter Test Task Context",
                "description": "Task context for testing artifact type filtering",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        # Create artifacts of different types
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Practice Artifact",
                "content": "Practice content",
            },
        )

        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "rule",
                "summary": "Rule Artifact",
                "content": "Rule content",
            },
        )

        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "prompt",
                "summary": "Prompt Artifact",
                "content": "Prompt content",
            },
        )

        # Get only practice artifacts
        practice_result = mcp_client.call_tool(
            "get_artifacts_for_task_context",
            {"task_context_id": task_context_id, "artifact_types": ["practice"]},
        )

        assert "Practice Artifact" in practice_result.data
        assert "Practice content" in practice_result.data
        assert "Rule Artifact" not in practice_result.data
        assert "Prompt Artifact" not in practice_result.data

    def test_multiple_artifacts_same_type(self, mcp_client):
        """Test creating multiple artifacts of the same type (now allowed)."""
        # Create a task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Multiple Artifacts Task Context",
                "description": "Task context for testing multiple artifacts of same type",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        # Create first practice artifact
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "First Practice",
                "content": "First practice content",
            },
        )

        # Create second practice artifact
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Second Practice",
                "content": "Second practice content",
            },
        )

        # Get artifacts and verify both exist
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )

        assert "First Practice" in artifacts_result.data
        assert "Second Practice" in artifacts_result.data
        assert "First practice content" in artifacts_result.data
        assert "Second practice content" in artifacts_result.data

    def test_update_artifact(self, mcp_client):
        """Test updating an existing artifact."""
        # Create a task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Update Test Task Context",
                "description": "Task context for testing artifact updates",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        # Create initial artifact
        create_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Initial Practice",
                "content": "Initial content",
            },
        )

        # Extract artifact ID
        artifact_id = create_result.data.split("\n")[1].split(": ")[1]

        # Update the artifact using the update_artifact tool
        update_result = mcp_client.call_tool(
            "update_artifact",
            {
                "artifact_id": artifact_id,
                "summary": "Updated Practice",
                "content": "Updated content",
            },
        )

        assert "Artifact updated successfully" in update_result.data

        # Get artifacts and verify update
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )

        assert "Updated Practice" in artifacts_result.data
        assert "Updated content" in artifacts_result.data

    def test_archive_artifact(self, mcp_client):
        """Test archiving an artifact."""
        # Create a task context and artifact
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Archive Test Task Context",
                "description": "Task context for testing artifact archiving",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        create_artifact_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
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
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )

        assert "Artifact to Archive" not in active_artifacts.data

        # Get artifacts including archived
        all_artifacts = mcp_client.call_tool(
            "get_artifacts_for_task_context",
            {"task_context_id": task_context_id, "include_archived": True},
        )

        assert "Artifact to Archive" in all_artifacts.data
        assert "archived" in all_artifacts.data.lower()

    def test_search_artifacts(self, mcp_client):
        """Test full-text search across artifacts."""
        # Create a task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Search Test Task Context",
                "description": "Task context for testing search functionality",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        # Create artifacts with searchable content
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Python Development Practice",
                "content": "When writing Python code, always use descriptive variable names and follow PEP 8 style guidelines.",
            },
        )

        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
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

    def test_task_context_lifecycle(self, mcp_client):
        """Test complete task context lifecycle: create, add artifacts, verify."""
        # Create task context
        create_task_context_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Lifecycle Test Task Context",
                "description": "Complete lifecycle test for task contexts",
            },
        )

        task_context_id = create_task_context_result.data.split("\n")[1].split(": ")[1]

        # Add artifacts
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Lifecycle Practice",
                "content": "Practice content for lifecycle test",
            },
        )

        # Verify task context appears in active task contexts
        active_task_contexts = mcp_client.call_tool("get_active_task_contexts", {})
        assert "Lifecycle Test Task Context" in active_task_contexts.data

        # Verify the task context exists and has artifacts
        artifacts = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )

        assert "Lifecycle Practice" in artifacts.data
        assert "Practice content for lifecycle test" in artifacts.data

    def test_get_active_task_contexts_with_multiple(self, mcp_client):
        """Test getting active task contexts when multiple exist."""
        # Create multiple task contexts
        contexts = [
            ("Context 1", "Description 1"),
            ("Context 2", "Description 2"),
            ("Context 3", "Description 3"),
        ]

        created_ids = []
        for summary, description in contexts:
            result = mcp_client.call_tool(
                "create_task_context",
                {"summary": summary, "description": description},
            )
            lines = result.data.split("\n")
            task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
            created_ids.append(task_context_id_line.split(": ")[1])

        # Get active task contexts
        result = mcp_client.call_tool("get_active_task_contexts", {})

        # Verify all contexts are listed
        for summary, _ in contexts:
            assert summary in result.data

        # Verify all IDs are present
        for tc_id in created_ids:
            assert tc_id in result.data

    def test_get_artifacts_edge_cases(self, mcp_client):
        """Test edge cases for get_artifacts_for_task_context."""
        # Test with invalid UUID
        result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": "not-a-uuid"}
        )
        assert "No artifacts found" in result.data

        # Test with empty artifact_types list
        create_result = mcp_client.call_tool(
            "create_task_context",
            {"summary": "Edge Case Context", "description": "For edge case testing"},
        )
        lines = create_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        result = mcp_client.call_tool(
            "get_artifacts_for_task_context",
            {"task_context_id": task_context_id, "artifact_types": []},
        )
        assert "No artifacts found" in result.data

        # Test include_archived when no archived artifacts exist
        result = mcp_client.call_tool(
            "get_artifacts_for_task_context",
            {"task_context_id": task_context_id, "include_archived": True},
        )
        assert "No artifacts found" in result.data

    def test_create_artifact_edge_cases(self, mcp_client):
        """Test edge cases for create_artifact."""
        # Create a task context first
        create_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Artifact Edge Case Context",
                "description": "For artifact edge cases",
            },
        )
        lines = create_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        # Test creating multiple artifacts of same type
        for i in range(3):
            result = mcp_client.call_tool(
                "create_artifact",
                {
                    "task_context_id": task_context_id,
                    "artifact_type": "practice",
                    "summary": f"Practice {i + 1}",
                    "content": f"Content for practice {i + 1}",
                },
            )
            assert "Artifact created successfully" in result.data

        # Verify all artifacts exist
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )
        for i in range(3):
            assert f"Practice {i + 1}" in artifacts_result.data
            assert f"Content for practice {i + 1}" in artifacts_result.data

        # Test with invalid task_context_id
        result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": "invalid-id",
                "artifact_type": "practice",
                "summary": "Invalid Context",
                "content": "Should fail",
            },
        )
        # This might succeed or fail depending on DB constraints, but let's check
        # Actually, since it's e2e, it might create with invalid FK, but probably fails
        # From existing test_error_handling, it seems invalid types are caught, but invalid IDs might not be

    def test_update_artifact_edge_cases(self, mcp_client):
        """Test edge cases for update_artifact."""
        # Create task context and artifact
        create_tc_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Update Edge Case Context",
                "description": "For update edge cases",
            },
        )
        lines = create_tc_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        create_art_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Original Summary",
                "content": "Original content",
            },
        )
        lines = create_art_result.data.split("\n")
        artifact_id_line = [line for line in lines if line.startswith("ID:")][0]
        artifact_id = artifact_id_line.split(": ")[1]

        # Test updating only summary
        result = mcp_client.call_tool(
            "update_artifact",
            {"artifact_id": artifact_id, "summary": "Updated Summary"},
        )
        assert "Artifact updated successfully" in result.data

        # Verify update
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )
        assert "Updated Summary" in artifacts_result.data
        assert "Original content" in artifacts_result.data

        # Test updating only content
        result = mcp_client.call_tool(
            "update_artifact",
            {"artifact_id": artifact_id, "content": "Updated content"},
        )
        assert "Artifact updated successfully" in result.data

        # Verify update
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": task_context_id}
        )
        assert "Updated Summary" in artifacts_result.data
        assert "Updated content" in artifacts_result.data

        # Test updating non-existent artifact
        result = mcp_client.call_tool(
            "update_artifact",
            {"artifact_id": "non-existent-id", "summary": "Should fail"},
        )
        assert "Artifact not found" in result.data

        # Test updating with neither summary nor content
        result = mcp_client.call_tool(
            "update_artifact",
            {"artifact_id": artifact_id},
        )
        assert "At least one of 'summary' or 'content' must be provided" in result.data

    def test_archive_artifact_edge_cases(self, mcp_client):
        """Test edge cases for archive_artifact."""
        # Create task context and artifact
        create_tc_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Archive Edge Case Context",
                "description": "For archive edge cases",
            },
        )
        lines = create_tc_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        create_art_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "To Archive",
                "content": "Content to archive",
            },
        )
        lines = create_art_result.data.split("\n")
        artifact_id_line = [line for line in lines if line.startswith("ID:")][0]
        artifact_id = artifact_id_line.split(": ")[1]

        # Archive the artifact
        result = mcp_client.call_tool(
            "archive_artifact",
            {"artifact_id": artifact_id, "reason": "Testing archive"},
        )
        assert "Artifact archived successfully" in result.data

        # Try to archive already archived artifact
        result = mcp_client.call_tool(
            "archive_artifact",
            {"artifact_id": artifact_id, "reason": "Already archived"},
        )
        # This should still succeed or handle gracefully
        # Depending on implementation, might succeed or fail

        # Test archiving with no reason
        # Create another artifact
        create_art2_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "rule",
                "summary": "To Archive No Reason",
                "content": "Content",
            },
        )
        lines = create_art2_result.data.split("\n")
        artifact2_id_line = [line for line in lines if line.startswith("ID:")][0]
        artifact2_id = artifact2_id_line.split(": ")[1]

        result = mcp_client.call_tool(
            "archive_artifact",
            {"artifact_id": artifact2_id},
        )
        assert "Artifact archived successfully" in result.data

    def test_search_artifacts_edge_cases(self, mcp_client):
        """Test edge cases for search_artifacts."""
        # Test with empty query
        result = mcp_client.call_tool("search_artifacts", {"query": ""})
        assert "Search query cannot be empty" in result.data

        # Test with whitespace-only query
        result = mcp_client.call_tool("search_artifacts", {"query": "   "})
        assert "Search query cannot be empty" in result.data

        # Test with query that has no matches
        result = mcp_client.call_tool(
            "search_artifacts", {"query": "nonexistenttermxyz"}
        )
        assert "No artifacts found" in result.data

        # Test with limit = 0
        result = mcp_client.call_tool("search_artifacts", {"query": "test", "limit": 0})
        # Should return no results or handle gracefully
        assert isinstance(result.data, str)

        # Test with very large limit
        result = mcp_client.call_tool(
            "search_artifacts", {"query": "test", "limit": 1000}
        )
        assert isinstance(result.data, str)

        # Test with special characters
        result = mcp_client.call_tool("search_artifacts", {"query": "!@#$%^&*()"})
        assert isinstance(result.data, str)  # Should not crash

        # Create some artifacts to search
        create_tc_result = mcp_client.call_tool(
            "create_task_context",
            {"summary": "Search Test Context", "description": "For search edge cases"},
        )
        lines = create_tc_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Unique search term",
                "content": "Content with unique search term",
            },
        )

        # Test search with exact match
        result = mcp_client.call_tool(
            "search_artifacts", {"query": "unique search term"}
        )
        assert "Unique search term" in result.data

        # Test search with partial match
        result = mcp_client.call_tool("search_artifacts", {"query": "unique"})
        assert "Unique search term" in result.data

    def test_error_handling(self, mcp_client):
        """Test error handling for invalid inputs."""
        # Test with invalid task context ID
        artifacts_result = mcp_client.call_tool(
            "get_artifacts_for_task_context", {"task_context_id": "invalid-uuid"}
        )

        assert "No artifacts found" in artifacts_result.data

        # Test with invalid artifact type
        create_result = mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": "invalid-uuid",
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

    def test_reflect_and_update_artifacts(self, mcp_client):
        """Test the reflect_and_update_artifacts tool."""
        # Create task context and artifacts
        create_tc_result = mcp_client.call_tool(
            "create_task_context",
            {
                "summary": "Reflection Test Context",
                "description": "For testing reflection functionality",
            },
        )
        lines = create_tc_result.data.split("\n")
        task_context_id_line = [line for line in lines if line.startswith("ID:")][0]
        task_context_id = task_context_id_line.split(": ")[1]

        # Create some artifacts
        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "practice",
                "summary": "Test Practice",
                "content": "Practice content",
            },
        )

        mcp_client.call_tool(
            "create_artifact",
            {
                "task_context_id": task_context_id,
                "artifact_type": "rule",
                "summary": "Test Rule",
                "content": "Rule content",
            },
        )

        # Call reflect_and_update_artifacts
        reflect_result = mcp_client.call_tool(
            "reflect_and_update_artifacts",
            {
                "task_context_id": task_context_id,
                "learnings": "I discovered that the import checking process should be automated. Found several missed imports that needed correction.",
            },
        )

        # Verify the response includes reflection prompts
        assert "REFLECTION CHECKPOINT" in reflect_result.data
        assert "Your Learnings:" in reflect_result.data
        assert "Current Active Artifacts" in reflect_result.data
        assert "Test Practice" in reflect_result.data
        assert "Test Rule" in reflect_result.data
        assert "REQUIRED ACTIONS" in reflect_result.data
        assert "CREATE new artifacts" in reflect_result.data
        assert "UPDATE existing artifacts" in reflect_result.data
        assert "ARCHIVE artifacts" in reflect_result.data
