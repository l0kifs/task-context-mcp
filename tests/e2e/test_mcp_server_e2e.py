# E2E tests for MCP server with real client connection

"""End-to-end tests for MCP server using real HTTP client connections."""

import json

from fastmcp import Client
import pytest


class TestMCPServerE2E:
    """End-to-end tests for MCP server functionality."""

    @pytest.mark.asyncio
    async def test_create_and_get_task(self, mcp_server_url: str) -> None:
        """Test creating a task and retrieving it."""
        async with Client(mcp_server_url) as client:
            # Create a task
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Test Task",
                    "description": "A test task for E2E testing",
                    "project_name": "test-project",
                },
            )

            assert result is not None
            # Access the content from CallToolResult - it's a list of TextContent
            content = result.content[0].text
            task_data = json.loads(content)
            assert "task_id" in task_data
            task_id = task_data["task_id"]

            # Get the task back
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            assert task_result is not None
            task_content = task_result.content[0].text
            task_details = json.loads(task_content)
            assert task_details["task"]["title"] == "Test Task"
            assert task_details["task"]["description"] == "A test task for E2E testing"
            assert task_details["task"]["project_name"] == "test-project"

    @pytest.mark.asyncio
    async def test_create_task_with_steps_immediately(
        self, mcp_server_url: str
    ) -> None:
        """Test creating a task with steps immediately in one call."""
        async with Client(mcp_server_url) as client:
            # Create a task with steps in one call
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Task with Immediate Steps",
                    "description": "Task created with steps in one API call",
                    "project_name": "immediate-steps-test",
                    "steps": [
                        {"name": "Step 1", "description": "First step"},
                        {"name": "Step 2", "description": "Second step"},
                        {"name": "Step 3", "description": "Third step"},
                    ],
                },
            )

            assert result is not None
            content = result.content[0].text
            task_data = json.loads(content)
            assert "task_id" in task_data
            task_id = task_data["task_id"]

            # Get the task back and verify steps were created
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            assert task_result is not None
            task_content = task_result.content[0].text
            task_details = json.loads(task_content)

            assert task_details["success"] is True
            assert task_details["task"]["title"] == "Task with Immediate Steps"
            assert (
                task_details["task"]["description"]
                == "Task created with steps in one API call"
            )
            assert task_details["task"]["project_name"] == "immediate-steps-test"
            assert len(task_details["task"]["steps"]) == 3

            # Verify step details
            assert task_details["task"]["steps"][0]["name"] == "Step 1"
            assert task_details["task"]["steps"][0]["description"] == "First step"
            assert task_details["task"]["steps"][0]["status"] == "pending"

            assert task_details["task"]["steps"][1]["name"] == "Step 2"
            assert task_details["task"]["steps"][1]["description"] == "Second step"
            assert task_details["task"]["steps"][1]["status"] == "pending"

            assert task_details["task"]["steps"][2]["name"] == "Step 3"
            assert task_details["task"]["steps"][2]["description"] == "Third step"
            assert task_details["task"]["steps"][2]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_task_with_empty_steps(self, mcp_server_url: str) -> None:
        """Test creating a task with empty steps list."""
        async with Client(mcp_server_url) as client:
            # Create a task with empty steps list
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Task with Empty Steps",
                    "description": "Task with no steps",
                    "project_name": "empty-steps-test",
                    "steps": [],
                },
            )

            assert result is not None
            content = result.content[0].text
            task_data = json.loads(content)
            assert "task_id" in task_data
            task_id = task_data["task_id"]

            # Verify task was created without steps
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            task_content = task_result.content[0].text
            task_details = json.loads(task_content)

            assert task_details["success"] is True
            assert task_details["task"]["title"] == "Task with Empty Steps"
            assert len(task_details["task"]["steps"]) == 0

    @pytest.mark.asyncio
    async def test_create_task_with_steps(self, mcp_server_url: str) -> None:
        """Test creating a task with steps."""
        async with Client(mcp_server_url) as client:
            # First create a task
            create_result = await client.call_tool(
                "create_task",
                {
                    "title": "Task with Steps",
                    "description": "Task with multiple steps",
                    "project_name": "test-project",
                },
            )
            create_data = json.loads(create_result.content[0].text)
            task_id = create_data["task_id"]

            # Then create steps for the task
            steps_result = await client.call_tool(
                "create_task_steps",
                {
                    "task_id": task_id,
                    "steps": [
                        {"step_number": 1, "description": "First step"},
                        {"step_number": 2, "description": "Second step"},
                        {"step_number": 3, "description": "Third step"},
                    ],
                },
            )
            steps_data = json.loads(steps_result.content[0].text)
            assert steps_data["success"] is True
            # Note: create_task_steps doesn't return task_id, just success message

            # Verify task was created with steps
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            task_data = json.loads(task_result.content[0].text)
            assert task_data["success"] is True
            assert len(task_data["task"]["steps"]) == 3
            assert task_data["task"]["steps"][0]["name"] == "Step 1"
            assert task_data["task"]["steps"][1]["name"] == "Step 2"
            assert task_data["task"]["steps"][2]["name"] == "Step 3"

    @pytest.mark.asyncio
    async def test_update_task_steps(self, mcp_server_url: str) -> None:
        """Test updating task steps."""
        async with Client(mcp_server_url) as client:
            # Create a task first
            create_result = await client.call_tool(
                "create_task",
                {
                    "title": "Task for Step Updates",
                    "description": "Testing step updates",
                    "project_name": "test-project",
                },
            )
            create_data = json.loads(create_result.content[0].text)
            task_id = create_data["task_id"]

            # Create steps first
            await client.call_tool(
                "create_task_steps",
                {
                    "task_id": task_id,
                    "steps": [
                        {"step_number": 1, "description": "Step 1"},
                        {"step_number": 2, "description": "Step 2"},
                    ],
                },
            )

            # Update the steps
            update_result = await client.call_tool(
                "update_task_steps",
                {
                    "task_id": task_id,
                    "step_updates": [
                        {
                            "step_number": 1,
                            "status": "completed",
                            "description": "Updated step 1",
                        },
                        {"step_number": 2, "status": "pending"},
                    ],
                },
            )
            update_data = json.loads(update_result.content[0].text)
            assert update_data["success"] is True

    @pytest.mark.asyncio
    async def test_get_task_context(self, mcp_server_url: str) -> None:
        """Test getting task context."""
        async with Client(mcp_server_url) as client:
            # Create a task with context
            create_result = await client.call_tool(
                "create_task",
                {
                    "title": "Context Task",
                    "description": "Task for context testing",
                    "project_name": "context-project",
                },
            )
            create_data = json.loads(create_result.content[0].text)
            task_id = create_data["task_id"]

            # Create steps for the task
            await client.call_tool(
                "create_task_steps",
                {
                    "task_id": task_id,
                    "steps": [
                        {"step_number": 1, "description": "Research phase"},
                        {"step_number": 2, "description": "Implementation phase"},
                    ],
                },
            )

            # Get task context
            context_result = await client.call_tool(
                "get_task_context", {"task_id": task_id}
            )
            context_data = json.loads(context_result.content[0].text)

            assert context_data["success"] is True
            assert "context" in context_data
            assert context_data["context"]["title"] == "Context Task"
            assert context_data["context"]["total_steps"] == 2

    @pytest.mark.asyncio
    async def test_list_tasks(self, mcp_server_url: str) -> None:
        """Test listing tasks."""
        async with Client(mcp_server_url) as client:
            # Create multiple tasks
            task_ids = []
            for i in range(3):
                result = await client.call_tool(
                    "create_task",
                    {
                        "title": f"List Task {i}",
                        "description": f"Task {i} for listing",
                        "project_name": "list-test",
                    },
                )
                result_data = json.loads(result.content[0].text)
                task_ids.append(result_data["task_id"])

            # List all tasks
            list_result = await client.call_tool("list_tasks", {})
            list_data = json.loads(list_result.content[0].text)

            assert list_data["success"] is True
            assert "tasks" in list_data
            assert len(list_data["tasks"]) >= 3

            # Verify our tasks are in the list
            task_titles = [task["title"] for task in list_data["tasks"]]
            assert "List Task 0" in task_titles
            assert "List Task 1" in task_titles
            assert "List Task 2" in task_titles

    @pytest.mark.asyncio
    async def test_update_task_status(self, mcp_server_url: str) -> None:
        """Test updating task status."""
        async with Client(mcp_server_url) as client:
            # Create a task
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Status Update Task",
                    "description": "Testing status updates",
                    "project_name": "status-test",
                },
            )
            result_data = json.loads(result.content[0].text)
            task_id = result_data["task_id"]

            # Update task status
            update_result = await client.call_tool(
                "update_task_status", {"task_id": task_id, "status": "in_progress"}
            )
            update_data = json.loads(update_result.content[0].text)

            assert update_data["success"] is True

            # Verify status was updated
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            task_data = json.loads(task_result.content[0].text)
            assert task_data["task"]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_update_task(self, mcp_server_url: str) -> None:
        """Test updating task details."""
        async with Client(mcp_server_url) as client:
            # Create a task
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Original Title",
                    "description": "Original description",
                    "project_name": "update-test",
                },
            )
            result_data = json.loads(result.content[0].text)
            task_id = result_data["task_id"]

            # Update task
            update_result = await client.call_tool(
                "update_task",
                {
                    "task_id": task_id,
                    "title": "Updated Title",
                    "description": "Updated description",
                },
            )
            update_data = json.loads(update_result.content[0].text)

            assert update_data["success"] is True

            # Verify task was updated
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            task_data = json.loads(task_result.content[0].text)
            assert task_data["task"]["title"] == "Updated Title"
            assert task_data["task"]["description"] == "Updated description"
            assert (
                task_data["task"]["project_name"] == "update-test"
            )  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_get_tasks_by_project(self, mcp_server_url: str) -> None:
        """Test getting tasks by project."""
        async with Client(mcp_server_url) as client:
            # Create tasks in different projects
            project_a_tasks = []
            project_b_tasks = []

            for i in range(2):
                result_a = await client.call_tool(
                    "create_task",
                    {
                        "title": f"Project A Task {i}",
                        "description": "Task in project A",
                        "project_name": "project-a",
                    },
                )
                result_a_data = json.loads(result_a.content[0].text)
                project_a_tasks.append(result_a_data["task_id"])

                result_b = await client.call_tool(
                    "create_task",
                    {
                        "title": f"Project B Task {i}",
                        "description": "Task in project B",
                        "project_name": "project-b",
                    },
                )
                result_b_data = json.loads(result_b.content[0].text)
                project_b_tasks.append(result_b_data["task_id"])

            # Get tasks by project A
            project_a_result = await client.call_tool(
                "get_tasks_by_project", {"project_name": "project-a"}
            )
            project_a_data = json.loads(project_a_result.content[0].text)

            assert project_a_data["success"] is True
            assert "tasks" in project_a_data
            assert len(project_a_data["tasks"]) >= 2

            # Verify all tasks are from project A
            for task in project_a_data["tasks"]:
                assert task["project_name"] == "project-a"

            # Get tasks by project B
            project_b_result = await client.call_tool(
                "get_tasks_by_project", {"project_name": "project-b"}
            )
            project_b_data = json.loads(project_b_result.content[0].text)

            assert project_b_data["success"] is True
            assert "tasks" in project_b_data
            assert len(project_b_data["tasks"]) >= 2

            # Verify all tasks are from project B
            for task in project_b_data["tasks"]:
                assert task["project_name"] == "project-b"

    @pytest.mark.asyncio
    async def test_delete_task(self, mcp_server_url: str) -> None:
        """Test deleting a task."""
        async with Client(mcp_server_url) as client:
            # Create a task
            result = await client.call_tool(
                "create_task",
                {
                    "title": "Task to Delete",
                    "description": "This task will be deleted",
                    "project_name": "delete-test",
                },
            )
            result_data = json.loads(result.content[0].text)
            task_id = result_data["task_id"]

            # Verify task exists
            task_result = await client.call_tool("get_task", {"task_id": task_id})
            task_data = json.loads(task_result.content[0].text)
            assert task_data["success"] is True

            # Delete the task
            delete_result = await client.call_tool("delete_task", {"task_id": task_id})
            delete_data = json.loads(delete_result.content[0].text)

            assert delete_data["success"] is True

            # Verify task no longer exists (should raise an exception or return error)
            task_result_after = await client.call_tool("get_task", {"task_id": task_id})
            task_data_after = json.loads(task_result_after.content[0].text)
            assert task_data_after["success"] is False

    @pytest.mark.asyncio
    async def test_task_workflow(self, mcp_server_url: str) -> None:
        """Test a complete task workflow."""
        async with Client(mcp_server_url) as client:
            # 1. Create task
            create_result = await client.call_tool(
                "create_task",
                {
                    "title": "Workflow Task",
                    "description": "Complete workflow test",
                    "project_name": "workflow-test",
                },
            )
            create_data = json.loads(create_result.content[0].text)
            task_id = create_data["task_id"]

            # 2. Create steps for the task
            await client.call_tool(
                "create_task_steps",
                {
                    "task_id": task_id,
                    "steps": [
                        {"step_number": 1, "description": "Plan the work"},
                        {"step_number": 2, "description": "Execute the plan"},
                        {"step_number": 3, "description": "Review the results"},
                    ],
                },
            )

            # 3. Update status to in progress
            await client.call_tool(
                "update_task_status", {"task_id": task_id, "status": "in_progress"}
            )

            # 4. Update steps (mark planning as complete)
            await client.call_tool(
                "update_task_steps",
                {
                    "task_id": task_id,
                    "step_updates": [
                        {
                            "step_number": 1,
                            "status": "completed",
                            "description": "Plan the work",
                        },
                        {"step_number": 2, "status": "pending"},
                    ],
                },
            )

            # 5. Get task context to verify workflow
            context_result = await client.call_tool(
                "get_task_context", {"task_id": task_id}
            )
            context_data = json.loads(context_result.content[0].text)

            assert context_data["success"] is True
            assert context_data["context"]["status"] == "in_progress"
            assert context_data["context"]["total_steps"] == 3

            # 6. Complete the task
            await client.call_tool(
                "update_task_status", {"task_id": task_id, "status": "completed"}
            )
