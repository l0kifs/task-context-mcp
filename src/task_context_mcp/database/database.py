from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..config.settings import get_settings
from .models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    Base,
    Task,
    TaskStatus,
)


class DatabaseManager:
    """Database manager class for handling database operations."""

    def __init__(self):
        self.settings = get_settings()
        self.engine = create_engine(self.settings.database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def init_db(self):
        """Initialize the database by creating tables."""
        Path(self.settings.data_dir).mkdir(exist_ok=True)
        self.create_tables()
        # Create FTS5 virtual table for full-text search
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
                    id, summary, content, task_id, tokenize='porter'
                );
            """)
            )
            conn.commit()

    @contextmanager
    def get_session(self):
        """Get a database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_task(
        self, summary: str, description: str, status: TaskStatus = TaskStatus.ACTIVE
    ):
        """Create a new task."""
        logger.info(f"Creating task: {summary}")
        with self.get_session() as session:
            task = Task(summary=summary, description=description, status=status.value)
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"Task created successfully: {task.id}")
            return task

    def update_task(
        self,
        task_id: str,
        summary: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
    ):
        """Update an existing task."""
        logger.info(f"Updating task: {task_id}")
        with self.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                if summary is not None:
                    task.summary = summary
                if description is not None:
                    task.description = description
                if status is not None:
                    task.status = status.value
                session.commit()
                session.refresh(task)
                logger.info(f"Task updated successfully: {task_id}")
                return task
            else:
                logger.warning(f"Task not found: {task_id}")
                return None

    def archive_task(self, task_id: str):
        """Archive a task by setting its status to ARCHIVED."""
        logger.info(f"Archiving task: {task_id}")
        with self.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.ARCHIVED.value
                session.commit()
                session.refresh(task)
                logger.info(f"Task archived successfully: {task_id}")
                return task
            else:
                logger.warning(f"Task not found: {task_id}")
                return None

    def get_active_tasks(self):
        """Get all active tasks."""
        logger.info("Getting all active tasks")
        with self.get_session() as session:
            tasks = (
                session.query(Task).filter(Task.status == TaskStatus.ACTIVE.value).all()
            )
            logger.info(f"Retrieved {len(tasks)} active tasks")
            return tasks

    def create_artifact(
        self,
        task_id: str,
        artifact_type: ArtifactType,
        content: str,
        summary: str,
        status: ArtifactStatus = ArtifactStatus.ACTIVE,
    ):
        """Create a new artifact or update existing one for the task and type."""
        logger.info(
            f"Creating/updating artifact for task {task_id}, type {artifact_type}"
        )
        with self.get_session() as session:
            # Find existing artifact for this task and type, or create new
            artifact = (
                session.query(Artifact)
                .filter(
                    Artifact.task_id == task_id,
                    Artifact.artifact_type == artifact_type.value,
                )
                .first()
            )
            if not artifact:
                logger.debug(
                    f"Creating new artifact for task {task_id}, type {artifact_type}"
                )
                artifact = Artifact(
                    task_id=task_id,
                    artifact_type=artifact_type.value,
                    summary=summary,
                    content=content,
                    status=status.value,
                )
                session.add(artifact)
            else:
                logger.debug(
                    f"Updating existing artifact for task {task_id}, type {artifact_type}"
                )
                artifact.summary = summary
                artifact.content = content
                artifact.status = status.value
            session.commit()
            session.refresh(artifact)
            # Insert or update FTS5 table
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                    INSERT OR REPLACE INTO artifacts_fts (id, summary, content, task_id)
                    VALUES (:id, :summary, :content, :task_id)
                """),
                    {
                        "id": artifact.id,
                        "summary": artifact.summary,
                        "content": artifact.content,
                        "task_id": artifact.task_id,
                    },
                )
                conn.commit()
            logger.info(f"Artifact created/updated successfully: {artifact.id}")
            return artifact

    def archive_artifact(self, artifact_id: str, reason: str | None = None):
        """Archive an artifact by setting its status to ARCHIVED."""
        logger.info(f"Archiving artifact: {artifact_id}")
        with self.get_session() as session:
            artifact = (
                session.query(Artifact).filter(Artifact.id == artifact_id).first()
            )
            if artifact:
                artifact.status = ArtifactStatus.ARCHIVED.value
                artifact.archived_at = datetime.now(timezone.utc)
                artifact.archivation_reason = reason
                session.commit()
                session.refresh(artifact)
                # Remove from FTS5 table
                with self.engine.connect() as conn:
                    conn.execute(
                        text("DELETE FROM artifacts_fts WHERE id = :id"),
                        {"id": artifact_id},
                    )
                    conn.commit()
                logger.info(f"Artifact archived successfully: {artifact_id}")
                return artifact
            else:
                logger.warning(f"Artifact not found: {artifact_id}")
                return None

    def get_artifacts_for_task(
        self,
        task_id: str,
        artifact_types: list[ArtifactType] | None = None,
        status: ArtifactStatus | None = None,
    ):
        """Get artifacts for a task"""
        logger.info(f"Getting artifacts for task: {task_id}")
        with self.get_session() as session:
            query = session.query(Artifact).filter(Artifact.task_id == task_id)
            if artifact_types:
                query = query.filter(
                    Artifact.artifact_type.in_([t.value for t in artifact_types])
                )
            if status:
                query = query.filter(Artifact.status == status.value)
            else:
                query = query.filter(Artifact.status == ArtifactStatus.ACTIVE.value)
            results = query.all()
            logger.info(f"Retrieved {len(results)} artifacts for task {task_id}")
            return results

    def search_artifacts(self, query: str, limit: int = 10):
        """Search artifacts using full-text search."""
        logger.info(f"Searching artifacts with query: {query}")
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT id, summary, content, task_id, rank
                FROM artifacts_fts
                WHERE artifacts_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """),
                {"query": query, "limit": limit},
            )
            rows = result.fetchall()
            logger.info(f"Found {len(rows)} matching artifacts")
            return rows


# Global instance for convenience
db_manager = DatabaseManager()
