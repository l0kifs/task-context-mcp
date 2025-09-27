"""Domain models and entities for the Task Context MCP application."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskStatus:
    """Task status constants."""

    OPEN = "open"
    COMPLETED = "completed"


class Task(BaseModel):
    """
    Task entity representing a user task.

    This is a domain entity that represents a task with its core attributes.
    """

    id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    status: str
    created_at: datetime
    updated_at: datetime
    summaries: list["TaskSummary"] = Field(default_factory=list, exclude=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate task status."""
        if v not in [TaskStatus.OPEN, TaskStatus.COMPLETED]:
            msg = f"Invalid task status: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_title_not_empty(self) -> "Task":
        """Validate that title is not empty after model construction."""
        if not self.title or not self.title.strip():
            msg = "Task title cannot be empty"
            raise ValueError(msg)
        return self

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now(UTC)

    def mark_open(self) -> None:
        """Mark task as open."""
        self.status = TaskStatus.OPEN
        self.updated_at = datetime.now(UTC)


class TaskSummary(BaseModel):
    """
    Task summary entity representing a step summary.

    This represents a summary of work done in a specific step of a task.
    """

    id: int | None = None
    task_id: int = Field(..., gt=0)
    step_number: int = Field(..., ge=1)
    summary: str = Field(..., min_length=1, max_length=5000)
    created_at: datetime
