import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models import Base, Task, TaskSummary, DatabaseManager


@pytest.fixture
def db_manager():
    """Фикстура для тестовой базы данных"""
    # Используем in-memory SQLite для тестов
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


def test_create_task(db_manager):
    """Тест создания задачи"""
    with db_manager.get_session() as session:
        task = Task(title="Test Task", description="Test Description")
        session.add(task)
        session.commit()
        session.refresh(task)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.created_at is not None


def test_create_task_summary(db_manager):
    """Тест создания summary для задачи"""
    with db_manager.get_session() as session:
        # Создаем задачу
        task = Task(title="Test Task")
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Создаем summary
        summary = TaskSummary(
            task_id=task.id,
            step_number=1,
            summary="Test summary for step 1"
        )
        session.add(summary)
        session.commit()
        session.refresh(summary)
        
        assert summary.id is not None
        assert summary.task_id == task.id
        assert summary.step_number == 1
        assert summary.summary == "Test summary for step 1"


def test_task_summary_relationship(db_manager):
    """Тест связи между задачей и summary"""
    with db_manager.get_session() as session:
        # Создаем задачу
        task = Task(title="Test Task")
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Создаем несколько summary
        summary1 = TaskSummary(task_id=task.id, step_number=1, summary="Step 1")
        summary2 = TaskSummary(task_id=task.id, step_number=2, summary="Step 2")
        
        session.add_all([summary1, summary2])
        session.commit()
        
        # Проверяем связь
        from sqlalchemy.orm import selectinload
        
        loaded_task = session.query(Task).options(selectinload(Task.summaries)).filter(Task.id == task.id).first()
        
        assert len(loaded_task.summaries) == 2
        assert loaded_task.summaries[0].step_number in [1, 2]
        assert loaded_task.summaries[1].step_number in [1, 2] 