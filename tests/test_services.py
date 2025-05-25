import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import DatabaseManager
from app.services import TaskService


@pytest.fixture
async def task_service():
    """Фикстура для тестового сервиса задач"""
    db_manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await db_manager.create_tables()
    return TaskService(db_manager)


@pytest.mark.asyncio
async def test_create_task(task_service):
    """Тест создания задачи через сервис"""
    task_id = await task_service.create_task(
        title="Test Task",
        description="Test Description"
    )
    
    assert task_id is not None
    assert isinstance(task_id, int)
    assert task_id > 0


@pytest.mark.asyncio
async def test_get_task(task_service):
    """Тест получения задачи"""
    # Создаем задачу
    task_id = await task_service.create_task("Test Task", "Test Description")
    
    # Получаем задачу
    task_data = await task_service.get_task(task_id)
    
    assert task_data is not None
    assert task_data["id"] == task_id
    assert task_data["title"] == "Test Task"
    assert task_data["description"] == "Test Description"
    assert "created_at" in task_data
    assert "updated_at" in task_data
    assert task_data["summaries"] == []


@pytest.mark.asyncio
async def test_save_and_get_summary(task_service):
    """Тест сохранения и получения summary"""
    # Создаем задачу
    task_id = await task_service.create_task("Test Task")
    
    # Сохраняем summary
    success = await task_service.save_summary(task_id, 1, "Test summary for step 1")
    assert success is True
    
    # Получаем задачу с summary
    task_data = await task_service.get_task(task_id)
    assert len(task_data["summaries"]) == 1
    assert task_data["summaries"][0]["step_number"] == 1
    assert task_data["summaries"][0]["summary"] == "Test summary for step 1"


@pytest.mark.asyncio
async def test_update_existing_summary(task_service):
    """Тест обновления существующего summary"""
    # Создаем задачу и summary
    task_id = await task_service.create_task("Test Task")
    await task_service.save_summary(task_id, 1, "Original summary")
    
    # Обновляем summary
    success = await task_service.save_summary(task_id, 1, "Updated summary")
    assert success is True
    
    # Проверяем обновление
    task_data = await task_service.get_task(task_id)
    assert len(task_data["summaries"]) == 1
    assert task_data["summaries"][0]["summary"] == "Updated summary"


@pytest.mark.asyncio
async def test_get_task_context(task_service):
    """Тест получения контекста задачи"""
    # Создаем задачу
    task_id = await task_service.create_task("Test Task", "Test Description")
    
    # Добавляем несколько summary
    await task_service.save_summary(task_id, 1, "Step 1 completed")
    await task_service.save_summary(task_id, 2, "Step 2 completed")
    
    # Получаем контекст
    context = await task_service.get_task_context(task_id)
    
    assert context is not None
    assert context["task_id"] == task_id
    assert context["title"] == "Test Task"
    assert context["description"] == "Test Description"
    assert context["total_steps"] == 2
    assert "Шаг 1: Step 1 completed" in context["context_summary"]
    assert "Шаг 2: Step 2 completed" in context["context_summary"]


@pytest.mark.asyncio
async def test_list_tasks(task_service):
    """Тест получения списка задач"""
    # Создаем несколько задач
    task_id1 = await task_service.create_task("Task 1")
    task_id2 = await task_service.create_task("Task 2")
    
    # Получаем список
    tasks = await task_service.list_tasks()
    
    assert len(tasks) == 2
    task_ids = [task["id"] for task in tasks]
    assert task_id1 in task_ids
    assert task_id2 in task_ids


@pytest.mark.asyncio
async def test_delete_task(task_service):
    """Тест удаления задачи"""
    # Создаем задачу с summary
    task_id = await task_service.create_task("Test Task")
    await task_service.save_summary(task_id, 1, "Test summary")
    
    # Удаляем задачу
    success = await task_service.delete_task(task_id)
    assert success is True
    
    # Проверяем, что задача удалена
    task_data = await task_service.get_task(task_id)
    assert task_data is None


@pytest.mark.asyncio
async def test_save_summary_nonexistent_task(task_service):
    """Тест сохранения summary для несуществующей задачи"""
    success = await task_service.save_summary(999, 1, "Test summary")
    assert success is False 