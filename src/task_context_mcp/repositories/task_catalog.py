"""Repository for task catalog management."""

from datetime import datetime, timezone
from typing import Optional

from chromadb import Collection
from loguru import logger

from ..database import get_task_catalog_collection, TaskTypeSchema


class TaskCatalogRepository:
    """Repository for managing task types."""

    def __init__(self):
        """Initialize the repository."""
        self.collection: Collection = get_task_catalog_collection()

    def register_task_type(self, task_type: str, description: str) -> TaskTypeSchema:
        """Register a new task type.

        Args:
            task_type: Unique task identifier
            description: Task purpose description

        Returns:
            Created task type schema
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Store in ChromaDB
        self.collection.add(
            ids=[task_type],
            documents=[description],
            metadatas=[{
                "task_type": task_type,
                "description": description,
                "created_at": now,
                "updated_at": now,
            }]
        )
        
        logger.info(f"Registered task type: {task_type}")
        
        return TaskTypeSchema(
            task_type=task_type,
            description=description,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def get_task_type(self, task_type: str) -> Optional[TaskTypeSchema]:
        """Retrieve task metadata.

        Args:
            task_type: Task type identifier

        Returns:
            Task type schema or None if not found
        """
        try:
            result = self.collection.get(ids=[task_type])
            
            if not result["ids"]:
                return None
            
            metadata = result["metadatas"][0]
            return TaskTypeSchema(
                task_type=metadata["task_type"],
                description=metadata["description"],
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
            )
        except Exception as e:
            logger.warning(f"Failed to get task type {task_type}: {e}")
            return None

    def list_task_types(self) -> list[TaskTypeSchema]:
        """List all registered task types.

        Returns:
            List of task type schemas
        """
        result = self.collection.get()
        
        task_types = []
        for metadata in result["metadatas"]:
            task_types.append(TaskTypeSchema(
                task_type=metadata["task_type"],
                description=metadata["description"],
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
            ))
        
        return task_types

    def update_task_type(self, task_type: str, description: str) -> TaskTypeSchema:
        """Modify task type description.

        Args:
            task_type: Task type identifier
            description: New description

        Returns:
            Updated task type schema
        """
        # Get existing metadata
        result = self.collection.get(ids=[task_type])
        if not result["ids"]:
            raise ValueError(f"Task type {task_type} not found")
        
        existing_metadata = result["metadatas"][0]
        now = datetime.now(timezone.utc).isoformat()
        
        # Update in ChromaDB
        self.collection.update(
            ids=[task_type],
            documents=[description],
            metadatas=[{
                "task_type": task_type,
                "description": description,
                "created_at": existing_metadata["created_at"],
                "updated_at": now,
            }]
        )
        
        logger.info(f"Updated task type: {task_type}")
        
        return TaskTypeSchema(
            task_type=task_type,
            description=description,
            created_at=datetime.fromisoformat(existing_metadata["created_at"]),
            updated_at=datetime.fromisoformat(now),
        )
