# E2E tests for MCP server with real client connection

"""End-to-end tests for MCP server using real HTTP client connections."""

from collections.abc import Generator
from contextlib import closing
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging for E2E tests
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _find_server_command() -> str:
    """Find the full path to the task-context-mcp command."""
    server_cmd = shutil.which("task-context-mcp")
    if not server_cmd:
        msg = "task-context-mcp command not found in PATH"
        raise RuntimeError(msg)
    return server_cmd


def _start_server_process(
    server_cmd: str, server_env: dict[str, str]
) -> subprocess.Popen:
    """Start the MCP server as a subprocess."""
    # Security check: ensure server_cmd is a safe executable path
    if not server_cmd or not isinstance(server_cmd, str):
        msg = "Invalid server command provided"
        raise ValueError(msg)

    # Additional security: ensure it's an absolute path and exists
    server_path = Path(server_cmd)
    if not server_path.is_absolute() or not server_path.is_file():
        msg = (
            f"Server command must be an absolute path to an existing file: {server_cmd}"
        )
        raise ValueError(msg)

    return subprocess.Popen(  # noqa: S603 - We validate the command above
        [server_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=server_env,
        text=True,
        bufsize=1,  # Line-buffered output
    )


def check_socket(host: str, port: int) -> bool:
    """
    Check if a socket is open and listening on the given host and port.

    Args:
        host: The hostname or IP address to check.
        port: The port number to check.

    Returns:
        True if the socket is open, False otherwise.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(1)  # 1-second timeout for the connection attempt
        try:
            result = sock.connect_ex((host, port))
        except OSError:
            return False
        else:
            return result == 0


def _wait_for_server_ready(
    server_process: subprocess.Popen,
    host: str,
    port: int,
    server_url: str,
    max_wait_time_seconds: int = 30,
) -> None:
    """Wait for the MCP server to become ready."""
    logger.info(
        "Waiting for MCP server to start at %s (max %ds)...",
        server_url,
        max_wait_time_seconds,
    )

    start_time = time.time()
    poll_interval_seconds = 0.5

    while time.time() - start_time < max_wait_time_seconds:
        if server_process.poll() is not None:
            # Process terminated
            _handle_server_termination(server_process)
            return

        if check_socket(host, port):
            logger.info(
                "MCP server started successfully and listening at %s",
                server_url,
            )
            return

        logger.debug("Still waiting for MCP server at %s:%s...", host, port)
        time.sleep(poll_interval_seconds)

    msg = (
        f"MCP server failed to start at {server_url} within timeout. Check server logs."
    )
    raise RuntimeError(msg)


def _handle_server_termination(server_process: subprocess.Popen) -> None:
    """Handle case when server process terminates prematurely."""
    logger.error(
        "MCP server process terminated prematurely. Exit code: %s",
        server_process.returncode,
    )

    # Log output for debugging
    if server_process.stdout:
        stdout, stderr = server_process.communicate(timeout=5)
        if stdout and stdout.strip():
            logger.error("Server stdout: %s", stdout.strip())
        if stderr and stderr.strip():
            logger.error("Server stderr: %s", stderr.strip())

    msg = (
        f"MCP server process terminated prematurely with code "
        f"{server_process.returncode}. Check server logs."
    )
    raise RuntimeError(msg)


def _terminate_server_gracefully(server_process: subprocess.Popen) -> None:
    """Terminate the server process gracefully."""
    logger.info("Stopping MCP server (PID: %s)...", server_process.pid)
    server_process.terminate()

    try:
        stdout, stderr = server_process.communicate(timeout=10)
        logger.info("MCP server terminated gracefully.")
        if stdout and stdout.strip():
            logger.debug("Final server stdout: %s", stdout.strip())
        if stderr and stderr.strip():
            logger.debug("Final server stderr: %s", stderr.strip())
    except subprocess.TimeoutExpired:
        _force_kill_server(server_process)


def _force_kill_server(server_process: subprocess.Popen) -> None:
    """Force kill the server process if graceful termination fails."""
    logger.warning(
        "MCP server did not terminate gracefully after 10s, sending SIGKILL..."
    )
    server_process.kill()
    try:
        stdout, stderr = server_process.communicate(timeout=5)
        logger.info("MCP server killed.")
        if stdout and stdout.strip():
            logger.debug("Final server stdout after SIGKILL: %s", stdout.strip())
        if stderr and stderr.strip():
            logger.debug("Final server stderr after SIGKILL: %s", stderr.strip())
    except subprocess.TimeoutExpired:
        logger.exception(
            "MCP server did not stop even after SIGKILL. "
            "Manual intervention may be needed."
        )


def _handle_already_terminated_server(
    server_process: subprocess.Popen, server_ready: bool
) -> None:
    """Handle case when server process has already terminated."""
    logger.info(
        "MCP server (PID: %s) already terminated with code %s.",
        server_process.pid,
        server_process.returncode,
    )
    # If it terminated before being ready, try to capture any output
    if not server_ready:
        try:
            stdout, stderr = server_process.communicate(timeout=1)
            if stdout and stdout.strip():
                logger.error("Server stdout (terminated early): %s", stdout.strip())
            if stderr and stderr.strip():
                logger.error("Server stderr (terminated early): %s", stderr.strip())
        except subprocess.TimeoutExpired:
            logger.debug("No further output from early-terminated server.")


def _cleanup_server_process(
    server_process: subprocess.Popen, server_ready: bool
) -> None:
    """Clean up the server process after tests."""
    if server_process.poll() is None:
        _terminate_server_gracefully(server_process)
    else:
        _handle_already_terminated_server(server_process, server_ready)


@pytest.fixture
def mcp_server_url() -> Generator[str, None, None]:
    """
    Pytest fixture to start and stop the MCP server for E2E tests.

    This fixture starts the MCP server as a subprocess on a dedicated port (8002)
    for E2E testing, waits for it to become ready, and ensures proper cleanup.

    Yields:
        The URL of the running MCP server (e.g., "http://localhost:8002/mcp").
    """
    server_process = None
    host = "localhost"
    port = 8002  # Dedicated port for E2E tests
    server_url = f"http://{host}:{port}/mcp"

    try:
        # Set environment variables for the server
        server_env = os.environ.copy()
        server_env["MCP_SERVER_PORT"] = str(port)
        server_env["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests
        server_env["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

        logger.info(
            "Starting MCP server for E2E testing with command: "
            "'task-context-mcp' on port %s",
            port,
        )

        # Find and start the server
        server_cmd = _find_server_command()
        server_process = _start_server_process(server_cmd, server_env)

        # Wait for the server to become ready
        _wait_for_server_ready(server_process, host, port, server_url)

        yield server_url  # Provide the server URL to the tests

    except Exception:
        logger.exception("Error during MCP server fixture setup")
        raise
    finally:
        # Ensure the server process is stopped after tests are done
        if server_process:
            _cleanup_server_process(server_process, True)  # Assume ready if we got here
        else:
            logger.info("MCP server process was not started or already cleaned up.")
