from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TaskStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ArtifactType(str, Enum):
    PRACTICE = "practice"
    RULE = "rule"
    PROMPT = "prompt"
    RESULT = "result"


class ArtifactStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()), doc="Unique identifier for the task")
    summary = Column(String, nullable=False, doc="Summary of the task. Used by agent to identify the task")
    description = Column(Text, nullable=False, doc="Detailed description of the task. Used by agent to identify the task")
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), doc="Timestamp when the task was created")
    updated_date = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Timestamp when the task was last updated",
    )
    status = Column(String, default=TaskStatus.ACTIVE.value, doc="Current status of the task")

    # Relationship to artifacts
    artifacts = relationship("Artifact", back_populates="task")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()), doc="Unique identifier for the artifact")
    summary = Column(Text, nullable=False, doc="Summary of the artifact. Used for quick reference")
    content = Column(Text, nullable=False, doc="Full content of the artifact")
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, doc="Identifier of the associated task")
    artifact_type = Column(String, nullable=False, doc="Type of the artifact")
    status = Column(String, default=ArtifactStatus.ACTIVE.value, doc="Current status of the artifact")
    archived_at = Column(DateTime, nullable=True, doc="Timestamp when the artifact was archived")
    archivation_reason = Column(Text, nullable=True, doc="Reason for archiving the artifact")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), doc="Timestamp when the artifact was created")

    # Relationship to task
    task = relationship("Task", back_populates="artifacts")
