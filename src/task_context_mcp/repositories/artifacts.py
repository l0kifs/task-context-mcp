"""Repository for artifact management with versioning."""

import json
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from chromadb import Collection
from loguru import logger

from ..database import (
    get_artifacts_collection,
    ArtifactSchema,
    ArtifactStatus,
    ArtifactType,
    ArtifactMetadata,
)
from ..services import generate_embedding


class ArtifactRepository:
    """Repository for managing artifacts with versioning."""

    def __init__(self):
        """Initialize the repository."""
        self.collection: Collection = get_artifacts_collection()

    def _make_artifact_id(self, artifact_id: str, version: int) -> str:
        """Create unique ID for artifact version."""
        return f"{artifact_id}_v{version}"

    def add_artifact(
        self,
        task_type: str,
        artifact_type: ArtifactType,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        artifact_id: Optional[str] = None,
    ) -> ArtifactSchema:
        """Create artifact with auto-versioning.

        Args:
            task_type: Associated task type
            artifact_type: Type of artifact
            content: Artifact content
            metadata: Additional metadata
            artifact_id: Optional ID (generates UUID if not provided)

        Returns:
            Created artifact schema
        """
        if not artifact_id:
            artifact_id = str(uuid.uuid4())
        
        version = 1
        now = datetime.now(timezone.utc)
        
        # Generate embedding for content
        embedding = generate_embedding(content)
        
        # Prepare metadata
        artifact_metadata = ArtifactMetadata(
            task_type=task_type,
            artifact_type=artifact_type.value,
            version=version,
            status=ArtifactStatus.ACTIVE.value,
            created_at=now.isoformat(),
        )
        
        # Combine metadata and filter out None values (ChromaDB doesn't support None)
        combined_metadata = {
            **artifact_metadata.model_dump(exclude_none=True),
            **{"artifact_id": artifact_id},
            **(metadata or {}),
        }
        combined_metadata = {k: v for k, v in combined_metadata.items() if v is not None}
        
        # Store in ChromaDB
        doc_id = self._make_artifact_id(artifact_id, version)
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[combined_metadata]
        )
        
        logger.info(f"Added artifact {artifact_id} v{version}")
        
        return ArtifactSchema(
            artifact_id=artifact_id,
            task_type=task_type,
            artifact_type=artifact_type,
            version=version,
            content=content,
            metadata=metadata or {},
            status=ArtifactStatus.ACTIVE,
            created_at=now,
        )

    def get_artifact(
        self,
        artifact_id: str,
        version: Optional[int] = None
    ) -> Optional[ArtifactSchema]:
        """Retrieve specific or latest artifact.

        Args:
            artifact_id: Artifact identifier
            version: Specific version (None for latest)

        Returns:
            Artifact schema or None if not found
        """
        try:
            if version is not None:
                # Get specific version
                doc_id = self._make_artifact_id(artifact_id, version)
                result = self.collection.get(ids=[doc_id])
            else:
                # Get all versions and find latest active
                result = self.collection.get(
                    where={"artifact_id": artifact_id}
                )
            
            if not result["ids"]:
                return None
            
            # Find the latest version or specific version
            latest_idx = 0
            latest_version = 0
            
            for idx, metadata in enumerate(result["metadatas"]):
                if version is not None:
                    if metadata["version"] == version:
                        latest_idx = idx
                        break
                else:
                    if metadata["version"] > latest_version:
                        latest_version = metadata["version"]
                        latest_idx = idx
            
            metadata = result["metadatas"][latest_idx]
            content = result["documents"][latest_idx]
            
            # Extract custom metadata (remove our standard fields)
            standard_fields = {
                "task_type", "artifact_type", "version", "status",
                "created_at", "deprecated_at", "deprecated_reason",
                "replacement_id", "artifact_id"
            }
            custom_metadata = {
                k: v for k, v in metadata.items()
                if k not in standard_fields
            }
            
            return ArtifactSchema(
                artifact_id=metadata["artifact_id"],
                task_type=metadata["task_type"],
                artifact_type=ArtifactType(metadata["artifact_type"]),
                version=metadata["version"],
                content=content,
                metadata=custom_metadata,
                status=ArtifactStatus(metadata["status"]),
                deprecated_at=datetime.fromisoformat(metadata["deprecated_at"]) if metadata.get("deprecated_at") else None,
                deprecated_reason=metadata.get("deprecated_reason"),
                replacement_id=metadata.get("replacement_id"),
                created_at=datetime.fromisoformat(metadata["created_at"]),
            )
            
        except Exception as e:
            logger.warning(f"Failed to get artifact {artifact_id}: {e}")
            return None

    def update_artifact(
        self,
        artifact_id: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ArtifactSchema:
        """Update artifact (creates new version).

        Args:
            artifact_id: Artifact identifier
            content: New content
            metadata: New metadata

        Returns:
            New version artifact schema
        """
        # Get latest version
        latest = self.get_artifact(artifact_id)
        if not latest:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        # Create new version
        new_version = latest.version + 1
        now = datetime.now(timezone.utc)
        
        # Generate embedding for new content
        embedding = generate_embedding(content)
        
        # Prepare metadata
        artifact_metadata = ArtifactMetadata(
            task_type=latest.task_type,
            artifact_type=latest.artifact_type.value,
            version=new_version,
            status=ArtifactStatus.ACTIVE.value,
            created_at=now.isoformat(),
        )
        
        # Combine metadata and filter out None values (ChromaDB doesn't support None)
        combined_metadata = {
            **artifact_metadata.model_dump(exclude_none=True),
            **{"artifact_id": artifact_id},
            **(metadata or {}),
        }
        combined_metadata = {k: v for k, v in combined_metadata.items() if v is not None}
        
        # Store new version in ChromaDB
        doc_id = self._make_artifact_id(artifact_id, new_version)
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[combined_metadata]
        )
        
        logger.info(f"Updated artifact {artifact_id} to v{new_version}")
        
        return ArtifactSchema(
            artifact_id=artifact_id,
            task_type=latest.task_type,
            artifact_type=latest.artifact_type,
            version=new_version,
            content=content,
            metadata=metadata or {},
            status=ArtifactStatus.ACTIVE,
            created_at=now,
        )

    def delete_artifact(
        self,
        artifact_id: str,
        reason: Optional[str] = None,
        replacement_id: Optional[str] = None,
    ) -> ArtifactSchema:
        """Soft delete artifact (status='archived').

        Args:
            artifact_id: Artifact identifier
            reason: Reason for deletion
            replacement_id: Optional replacement artifact ID

        Returns:
            Archived artifact schema
        """
        # Get latest version
        latest = self.get_artifact(artifact_id)
        if not latest:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        now = datetime.now(timezone.utc)
        
        # Update status in ChromaDB
        doc_id = self._make_artifact_id(artifact_id, latest.version)
        result = self.collection.get(ids=[doc_id])
        
        if result["ids"]:
            metadata = result["metadatas"][0]
            metadata["status"] = ArtifactStatus.ARCHIVED.value
            metadata["deprecated_at"] = now.isoformat()
            metadata["deprecated_reason"] = reason
            if replacement_id:
                metadata["replacement_id"] = replacement_id
            
            self.collection.update(
                ids=[doc_id],
                metadatas=[metadata]
            )
        
        logger.info(f"Archived artifact {artifact_id}")
        
        latest.status = ArtifactStatus.ARCHIVED
        latest.deprecated_at = now
        latest.deprecated_reason = reason
        latest.replacement_id = replacement_id
        
        return latest

    def list_artifacts(
        self,
        task_type: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        status: ArtifactStatus = ArtifactStatus.ACTIVE,
    ) -> list[ArtifactSchema]:
        """Filter and list artifacts.

        Args:
            task_type: Optional task type filter
            artifact_type: Optional artifact type filter
            status: Status filter (default: active)

        Returns:
            List of artifact schemas
        """
        # Build where clause (ChromaDB requires explicit $and for multiple conditions)
        conditions = [{"status": status.value}]
        if task_type:
            conditions.append({"task_type": task_type})
        if artifact_type:
            conditions.append({"artifact_type": artifact_type.value})
        
        if len(conditions) == 1:
            where = conditions[0]
        else:
            where = {"$and": conditions}
        
        result = self.collection.get(where=where)
        
        # Group by artifact_id and get latest version
        artifacts_by_id: dict[str, tuple[int, int]] = {}  # artifact_id -> (version, index)
        
        for idx, metadata in enumerate(result["metadatas"]):
            aid = metadata["artifact_id"]
            version = metadata["version"]
            
            if aid not in artifacts_by_id or version > artifacts_by_id[aid][0]:
                artifacts_by_id[aid] = (version, idx)
        
        # Build result list
        artifacts = []
        for version, idx in artifacts_by_id.values():
            metadata = result["metadatas"][idx]
            content = result["documents"][idx]
            
            # Extract custom metadata
            standard_fields = {
                "task_type", "artifact_type", "version", "status",
                "created_at", "deprecated_at", "deprecated_reason",
                "replacement_id", "artifact_id"
            }
            custom_metadata = {
                k: v for k, v in metadata.items()
                if k not in standard_fields
            }
            
            artifacts.append(ArtifactSchema(
                artifact_id=metadata["artifact_id"],
                task_type=metadata["task_type"],
                artifact_type=ArtifactType(metadata["artifact_type"]),
                version=metadata["version"],
                content=content,
                metadata=custom_metadata,
                status=ArtifactStatus(metadata["status"]),
                deprecated_at=datetime.fromisoformat(metadata["deprecated_at"]) if metadata.get("deprecated_at") else None,
                deprecated_reason=metadata.get("deprecated_reason"),
                replacement_id=metadata.get("replacement_id"),
                created_at=datetime.fromisoformat(metadata["created_at"]),
            ))
        
        return artifacts
