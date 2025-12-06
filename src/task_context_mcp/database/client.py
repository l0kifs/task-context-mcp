"""ChromaDB client singleton for embedded mode."""

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from ..config.settings import get_settings

# Disable ChromaDB telemetry globally
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "chromadb.telemetry.product.posthog.NullPosthog"

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    """Get or create ChromaDB client singleton.
    
    Returns:
        ChromaDB client instance configured for persistent storage
    """
    global _client
    
    if _client is None:
        settings = get_settings()
        logger.info(f"Initializing ChromaDB client at {settings.db_path}")
        
        _client = chromadb.PersistentClient(
            path=settings.db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
            ),
        )
        
        logger.info("ChromaDB client initialized successfully")
    
    return _client


def reset_client() -> None:
    """Reset the client singleton (mainly for testing)."""
    global _client
    if _client is not None:
        # Don't call reset() as it makes database readonly
        # Just clear the singleton
        _client = None
        logger.info("ChromaDB client reset")
