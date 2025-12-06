"""Collection management for ChromaDB."""

from chromadb import Collection, EmbeddingFunction
from loguru import logger
from typing import cast

from .client import get_client

# Collection names
TASK_CATALOG_COLLECTION = "task_catalog"
ARTIFACTS_COLLECTION = "artifacts"


class SimpleEmbeddingFunction(EmbeddingFunction):
    """Simple embedding function that doesn't require network access."""
    
    def __init__(self):
        """Initialize the embedding function."""
        super().__init__()
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        """Generate simple embeddings (384 dimensions of zeros).
        
        This is used for collections that don't need semantic search
        like task_catalog which is primarily for metadata storage.
        """
        return [[0.0] * 384 for _ in input]
    
    def name(self) -> str:
        """Return the name of this embedding function."""
        return "simple"
    
    def get_config(self) -> dict:
        """Return configuration for this embedding function."""
        return {"name": "simple", "dimension": 384}


# Use simple embedding function to avoid network calls
_default_ef = SimpleEmbeddingFunction()


def get_or_create_collection(name: str, metadata: dict | None = None, embedding_function=None) -> Collection:
    """Get or create a ChromaDB collection.
    
    Args:
        name: Collection name
        metadata: Optional metadata for the collection
        embedding_function: Optional embedding function (uses default if None)
        
    Returns:
        ChromaDB collection instance
    """
    client = get_client()
    
    try:
        collection = client.get_collection(name=name, embedding_function=embedding_function or _default_ef)
        logger.debug(f"Retrieved existing collection: {name}")
    except Exception:
        # ChromaDB requires non-empty metadata, provide default if None
        if not metadata:
            metadata = {"created_by": "task-context-mcp"}
        collection = client.create_collection(
            name=name,
            metadata=metadata,
            embedding_function=embedding_function or _default_ef,
        )
        logger.info(f"Created new collection: {name}")
    
    return collection


def get_task_catalog_collection() -> Collection:
    """Get or create the task catalog collection.
    
    Returns:
        Task catalog collection
    """
    return get_or_create_collection(
        TASK_CATALOG_COLLECTION,
        metadata={"description": "Task type registry"}
    )


def get_artifacts_collection() -> Collection:
    """Get or create the artifacts collection.
    
    Returns:
        Artifacts collection
    """
    return get_or_create_collection(
        ARTIFACTS_COLLECTION,
        metadata={"description": "Versioned artifacts with embeddings"}
    )


def list_collections() -> list[str]:
    """List all collection names.
    
    Returns:
        List of collection names
    """
    client = get_client()
    collections = client.list_collections()
    return [col.name for col in collections]


def delete_collection(name: str) -> None:
    """Delete a collection.
    
    Args:
        name: Collection name to delete
    """
    client = get_client()
    try:
        client.delete_collection(name=name)
        logger.info(f"Deleted collection: {name}")
    except Exception as e:
        logger.warning(f"Failed to delete collection {name}: {e}")
