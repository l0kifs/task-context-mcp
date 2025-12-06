"""Database module for ChromaDB integration."""

from .client import get_client, reset_client
from .collections import (
    ARTIFACTS_COLLECTION,
    TASK_CATALOG_COLLECTION,
    get_artifacts_collection,
    get_or_create_collection,
    get_task_catalog_collection,
    list_collections,
    delete_collection,
)
from .schemas import (
    ArtifactMetadata,
    ArtifactSchema,
    ArtifactStatus,
    ArtifactType,
    TaskTypeSchema,
)

__all__ = [
    "get_client",
    "reset_client",
    "ARTIFACTS_COLLECTION",
    "TASK_CATALOG_COLLECTION",
    "get_artifacts_collection",
    "get_or_create_collection",
    "get_task_catalog_collection",
    "list_collections",
    "delete_collection",
    "ArtifactMetadata",
    "ArtifactSchema",
    "ArtifactStatus",
    "ArtifactType",
    "TaskTypeSchema",
]
