"""Main entry point for the task-context-mcp MCP server."""

from fastmcp import FastMCP
from loguru import logger

from .config.logging import setup_logging
from .config.settings import get_settings

# Initialize FastMCP server
mcp = FastMCP("task-context-mcp")


def run():
    """Run the MCP server."""
    # Setup logging
    setup_logging()
    settings = get_settings()
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Database path: {settings.db_path}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    run()
