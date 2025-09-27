"""Logging configuration for the application."""

import sys

from loguru import logger

from task_context_mcp.config.settings import settings


def setup_logging(log_file: str | None = None) -> None:
    """
    Configure application logging.

    Args:
        log_file: Optional path to log file. If not specified,
            only console logging is used.
    """
    # Remove default loguru handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        colorize=not settings.debug,  # Disable colors in debug mode
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> "
        "- <white>{message}</white>",
    )

    # Add file handler if specified
    if log_file:
        logger.add(
            log_file,
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="1 week",
            enqueue=True,
            serialize=False,
        )

    # Set up logging for external libraries
    if settings.debug:
        # In debug mode, reduce noise from external libraries
        logger.disable("httpx")
        logger.disable("sqlalchemy.engine")


def get_logger(name: str):
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name for the logger

    Returns:
        Logger instance
    """
    return logger.bind(module=name)
