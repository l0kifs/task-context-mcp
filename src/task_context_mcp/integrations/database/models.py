"""SQLAlchemy ORM models for database integration."""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

from task_context_mcp.models.entities import TaskStatus

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
    status = Column(
        Enum(TaskStatus.OPEN, TaskStatus.COMPLETED, name="task_status"),
        default=TaskStatus.OPEN,
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationship to summaries
    summaries = relationship(
        "TaskSummaryORM", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TaskORM(id={self.id}, title='{self.title}')>"


class TaskSummaryORM(Base):
    """
    SQLAlchemy ORM model for TaskSummary entity.

    Maps the domain TaskSummary entity to database table.
    """

    __tablename__ = "task_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationship to task
    task = relationship("TaskORM", back_populates="summaries")

    def __repr__(self):
        return f"<TaskSummaryORM(id={self.id}, task_id={self.task_id}, step={self.step_number})>"
