"""Collection management for ChromaDB."""

from chromadb import Collection
from loguru import logger

from .client import get_client

# Collection names
TASK_CATALOG_COLLECTION = "task_catalog"
ARTIFACTS_COLLECTION = "artifacts"


def get_or_create_collection(name: str, metadata: dict | None = None) -> Collection:
    """Get or create a ChromaDB collection.
    
    Args:
        name: Collection name
        metadata: Optional metadata for the collection
        
    Returns:
        ChromaDB collection instance
    """
    client = get_client()
    
    try:
        collection = client.get_collection(name=name)
        logger.debug(f"Retrieved existing collection: {name}")
    except Exception:
        # ChromaDB requires non-empty metadata, provide default if None
        if not metadata:
            metadata = {"created_by": "task-context-mcp"}
        collection = client.create_collection(
            name=name,
            metadata=metadata,
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
