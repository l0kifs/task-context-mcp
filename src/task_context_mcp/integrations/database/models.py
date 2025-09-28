"""SQLAlchemy ORM models for database integration."""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

from task_context_mcp.models.entities import StepStatus, TaskStatus

Base = declarative_base()


class TaskORM(Base):
    """
    SQLAlchemy ORM model for Task entity.

    Maps the domain Task entity to database table.
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_name = Column(String(255), nullable=False)
    status = Column(
        Enum(
            TaskStatus.OPEN,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CLOSED,
            name="task_status",
        ),
        default=TaskStatus.OPEN,
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationship to steps
    steps = relationship("StepORM", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TaskORM(id={self.id}, title='{self.title}')>"


class StepORM(Base):
    """
    SQLAlchemy ORM model for Step entity.

    Maps the domain Step entity to database table.
    """

    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(
            StepStatus.PENDING,
            StepStatus.COMPLETED,
            StepStatus.CANCELLED,
            name="step_status",
        ),
        default=StepStatus.PENDING,
        nullable=False,
    )
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationship to task
    task = relationship("TaskORM", back_populates="steps")

    def __repr__(self):
        return f"<StepORM(id={self.id}, task_id={self.task_id}, name='{self.name}')>"
