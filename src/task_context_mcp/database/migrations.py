"""Database migration utilities using Alembic."""

from pathlib import Path

from alembic.config import Config
from loguru import logger

from alembic import command


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    project_root = Path(__file__).parent.parent.parent.parent
    alembic_ini = project_root / "alembic.ini"

    if not alembic_ini.exists():
        raise FileNotFoundError(
            f"Alembic configuration not found at {alembic_ini}. "
            "Run 'alembic init alembic' to initialize."
        )

    alembic_cfg = Config(str(alembic_ini))
    return alembic_cfg


def run_migrations() -> None:
    """Run all pending database migrations to head."""
    logger.info("Running database migrations...")
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


def create_migration(message: str, autogenerate: bool = True) -> None:
    """
    Create a new migration revision.

    Args:
        message: Migration description
        autogenerate: Auto-detect model changes (default: True)
    """
    logger.info(f"Creating new migration: {message}")
    try:
        alembic_cfg = get_alembic_config()
        if autogenerate:
            command.revision(alembic_cfg, message=message, autogenerate=True)
        else:
            command.revision(alembic_cfg, message=message)
        logger.info("Migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise


def get_current_revision() -> str | None:
    """Get the current database revision."""
    try:
        alembic_cfg = get_alembic_config()
        # This would need a database connection to check
        # For now, return None - can be enhanced later
        return None
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        return None


def downgrade_migration(revision: str = "-1") -> None:
    """
    Downgrade database to a previous revision.

    Args:
        revision: Target revision (default: -1 for one step back)
    """
    logger.info(f"Downgrading database to revision: {revision}")
    try:
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision)
        logger.info("Database downgrade completed successfully")
    except Exception as e:
        logger.error(f"Failed to downgrade: {e}")
        raise
