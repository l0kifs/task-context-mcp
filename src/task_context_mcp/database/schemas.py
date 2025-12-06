"""Database schemas for artifacts and task catalog."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Type of artifact stored in the system."""

    PRACTICE = "practice"
    RULE = "rule"
    PROMPT = "prompt"
    RESULT = "result"


class ArtifactStatus(str, Enum):
    """Status of an artifact."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class TaskTypeSchema(BaseModel):
    """Schema for task type catalog entry."""

    task_type: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Task purpose description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ArtifactSchema(BaseModel):
    """Schema for artifact storage with versioning."""

    artifact_id: str = Field(..., description="Unique artifact identifier")
    task_type: str = Field(..., description="Associated task type")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    version: int = Field(default=1, description="Version number")
    content: str = Field(..., description="Artifact content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    status: ArtifactStatus = Field(default=ArtifactStatus.ACTIVE, description="Artifact status")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecation timestamp")
    deprecated_reason: Optional[str] = Field(None, description="Reason for deprecation")
    replacement_id: Optional[str] = Field(None, description="ID of replacement artifact")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class ArtifactMetadata(BaseModel):
    """Metadata stored with artifact in ChromaDB."""

    task_type: str
    artifact_type: str
    version: int
    status: str
    created_at: str
    deprecated_at: Optional[str] = None
    deprecated_reason: Optional[str] = None
    replacement_id: Optional[str] = None
