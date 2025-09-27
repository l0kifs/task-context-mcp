"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from task_context_mcp.config.logging_config import get_logger
from task_context_mcp.config.settings import settings
from task_context_mcp.integrations.database.models import Base

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.

    Provides centralized database connection management with proper
    async session handling and connection pooling.
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL. If None, uses settings.
        """
        self.database_url = database_url or settings.database.url.get_secret_value()
        self._engine = None
        self._async_session = None

        logger.info(
            "Database manager initialized", url=self._mask_url(self.database_url)
        )

    async def initialize(self) -> None:
        """
        Initialize database engine and create tables.

        Must be called before using the database manager.
        """
        logger.info("Initializing database engine")

        self._engine = create_async_engine(
            self.database_url,
            echo=settings.database.echo,
            pool_pre_ping=True,  # Verify connections before use
        )

        self._async_session = async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        await self.create_tables()
        logger.info("Database initialized successfully")

    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            error_msg = "Database engine not initialized. Call initialize() first."
            raise RuntimeError(error_msg)

        logger.debug("Creating database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.debug("Database tables created")

    def get_session(self) -> AsyncSession:
        """
        Get a new async database session.

        Returns:
            New AsyncSession instance
        """
        if not self._async_session:
            error_msg = "Database not initialized. Call initialize() first."
            raise RuntimeError(error_msg)

        return self._async_session()

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            logger.info("Closing database connections")
            await self._engine.dispose()
            self._engine = None
            self._async_session = None
            logger.info("Database connections closed")

    def _mask_url(self, url: str) -> str:
        """
        Mask sensitive information in database URL for logging.

        Args:
            url: Database URL

        Returns:
            Masked URL safe for logging
        """
        # Simple masking - replace password if present
        if "://" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                # Has credentials, mask them
                before_at = rest.split("@")[0]
                after_at = rest.split("@")[1]
                if ":" in before_at:
                    user = before_at.split(":")[0]
                    masked = f"{user}:***@{after_at}"
                else:
                    masked = f"***@{after_at}"
                return f"{protocol}://{masked}"
        return url
