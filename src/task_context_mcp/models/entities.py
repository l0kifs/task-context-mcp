"""Domain models and entities for the Task Context MCP application."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskStatus:
    """Task status constants."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class StepStatus:
    """Step status constants."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """
    Task entity representing a user task.

    This is a domain entity that represents a task with its core attributes.
    """

    id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    project_name: str = Field(..., min_length=1, max_length=255)
    status: str
    created_at: datetime
    updated_at: datetime
    steps: list["Step"] = Field(default_factory=list, exclude=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate task status."""
        if v not in [TaskStatus.OPEN, TaskStatus.IN_PROGRESS, TaskStatus.CLOSED]:
            msg = f"Invalid task status: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_title_not_empty(self) -> "Task":
        """Validate that title is not empty after model construction."""
        if not self.title or not self.title.strip():
            msg = "Task title cannot be empty"
            raise ValueError(msg)
        if not self.project_name or not self.project_name.strip():
            msg = "Task project_name cannot be empty"
            raise ValueError(msg)
        return self

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.CLOSED

    def is_open(self) -> bool:
        """Check if task is open."""
        return self.status == TaskStatus.OPEN

    def is_in_progress(self) -> bool:
        """Check if task is in progress."""
        return self.status == TaskStatus.IN_PROGRESS

    def mark_open(self) -> None:
        """Mark task as open."""
        self.status = TaskStatus.OPEN
        self.updated_at = datetime.now(UTC)

    def mark_in_progress(self) -> None:
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(UTC)

    def mark_closed(self) -> None:
        """Mark task as closed."""
        self.status = TaskStatus.CLOSED
        self.updated_at = datetime.now(UTC)

    def update_status_based_on_steps(self) -> None:
        """
        Update task status based on step statuses.

        - If any step is completed and task was open -> in_progress
        - If all steps are completed or cancelled -> closed
        """
        if not self.steps:
            return

        completed_statuses = [StepStatus.COMPLETED, StepStatus.CANCELLED]
        has_completed_steps = any(
            step.status == StepStatus.COMPLETED for step in self.steps
        )
        all_steps_final = all(step.status in completed_statuses for step in self.steps)

        if has_completed_steps and self.status == TaskStatus.OPEN:
            self.mark_in_progress()
        elif all_steps_final:
            self.mark_closed()


class Step(BaseModel):
    """
    Step entity representing a task step.

    This represents a step within a task that needs to be completed.
    """

    id: int | None = None
    task_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    status: str = Field(default=StepStatus.PENDING)
    result: str | None = Field(None, max_length=5000)
    created_at: datetime
    updated_at: datetime

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate step status."""
        if v not in [StepStatus.PENDING, StepStatus.COMPLETED, StepStatus.CANCELLED]:
            msg = f"Invalid step status: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_name_not_empty(self) -> "Step":
        """Validate that name is not empty after model construction."""
        if not self.name or not self.name.strip():
            msg = "Step name cannot be empty"
            raise ValueError(msg)
        return self

    def is_pending(self) -> bool:
        """Check if step is pending."""
        return self.status == StepStatus.PENDING

    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status == StepStatus.COMPLETED

    def is_cancelled(self) -> bool:
        """Check if step is cancelled."""
        return self.status == StepStatus.CANCELLED

    def mark_pending(self) -> None:
        """Mark step as pending."""
        self.status = StepStatus.PENDING
        self.updated_at = datetime.now(UTC)

    def mark_completed(self, result: str | None = None) -> None:
        """Mark step as completed."""
        self.status = StepStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.now(UTC)

    def mark_cancelled(self) -> None:
        """Mark step as cancelled."""
        self.status = StepStatus.CANCELLED
        self.updated_at = datetime.now(UTC)
