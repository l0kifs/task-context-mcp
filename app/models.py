from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine, Enum
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()


class TaskStatus(enum.Enum):
    """Статусы задач"""
    OPEN = "open"
    COMPLETED = "completed"


class Task(Base):
    """Модель для хранения задач пользователя"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с summary
    summaries = relationship("TaskSummary", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}')>"


class TaskSummary(Base):
    """Модель для хранения summary по шагам задачи"""
    __tablename__ = "task_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с задачей
    task = relationship("Task", back_populates="summaries")
    
    def __repr__(self):
        return f"<TaskSummary(id={self.id}, task_id={self.task_id}, step={self.step_number})>"


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, database_url: str = "sqlite:///./tasks.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Создает таблицы в базе данных"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Возвращает синхронную сессию"""
        return self.session_factory() 