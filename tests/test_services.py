import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import DatabaseManager
from app.services import TaskService


@pytest.fixture
def task_service():
    """Фикстура для тестового сервиса задач"""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return TaskService(db_manager)


def test_create_task(task_service):
    """Тест создания задачи"""
    # Создаем задачу
    task_id = task_service.create_task(
        title="Test Task",
        description="Test Description"
    )
    
    assert task_id is not None
    assert isinstance(task_id, int)
    assert task_id > 0


def test_get_task(task_service):
    """Тест получения задачи"""
    # Создаем задачу
    task_id = task_service.create_task("Test Task", "Test Description")
    
    # Получаем задачу
    task_data = task_service.get_task(task_id)
    
    assert task_data is not None
    assert task_data["id"] == task_id
    assert task_data["title"] == "Test Task"
    assert task_data["description"] == "Test Description"
    assert task_data["status"] == "open"
    assert "created_at" in task_data
    assert "updated_at" in task_data
    assert task_data["summaries"] == []


def test_save_and_get_summary(task_service):
    """Тест сохранения и получения summary"""
    # Создаем задачу
    task_id = task_service.create_task("Test Task")
    
    # Сохраняем summary
    success = task_service.save_summary(task_id, 1, "Test summary for step 1")
    
    assert success is True
    
    # Проверяем, что summary сохранился
    task_data = task_service.get_task(task_id)
    assert len(task_data["summaries"]) == 1
    assert task_data["summaries"][0]["step_number"] == 1
    assert task_data["summaries"][0]["summary"] == "Test summary for step 1"


def test_update_existing_summary(task_service):
    """Тест обновления существующего summary"""
    # Создаем задачу и summary
    task_id = task_service.create_task("Test Task")
    task_service.save_summary(task_id, 1, "Original summary")
    
    # Обновляем summary
    success = task_service.save_summary(task_id, 1, "Updated summary")
    
    assert success is True
    
    # Проверяем обновление
    task_data = task_service.get_task(task_id)
    assert len(task_data["summaries"]) == 1
    assert task_data["summaries"][0]["summary"] == "Updated summary"


def test_get_task_context(task_service):
    """Тест получения контекста задачи"""
    # Создаем задачу
    task_id = task_service.create_task("Test Task", "Test Description")
    
    # Добавляем несколько summary
    task_service.save_summary(task_id, 1, "Step 1 completed")
    task_service.save_summary(task_id, 2, "Step 2 completed")
    
    # Получаем контекст
    context = task_service.get_task_context(task_id)
    
    assert context is not None
    assert context["task_id"] == task_id
    assert context["title"] == "Test Task"
    assert context["description"] == "Test Description"
    assert context["total_steps"] == 2
    assert "Шаг 1: Step 1 completed" in context["context_summary"]
    assert "Шаг 2: Step 2 completed" in context["context_summary"]
    assert "last_updated" in context


def test_list_tasks(task_service):
    """Тест получения списка задач"""
    # Создаем несколько задач
    task_id1 = task_service.create_task("Task 1")
    task_id2 = task_service.create_task("Task 2")
    
    # Получаем список
    result = task_service.list_tasks()
    
    assert "tasks" in result
    assert "pagination" in result
    assert len(result["tasks"]) == 2
    
    # Проверяем пагинацию
    pagination = result["pagination"]
    assert pagination["page"] == 1
    assert pagination["page_size"] == 10
    assert pagination["total_count"] == 2
    assert pagination["total_pages"] == 1
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is False
    
    # Проверяем данные задач
    task_ids = [task["id"] for task in result["tasks"]]
    assert task_id1 in task_ids
    assert task_id2 in task_ids


def test_delete_task(task_service):
    """Тест удаления задачи"""
    # Создаем задачу с summary
    task_id = task_service.create_task("Test Task")
    task_service.save_summary(task_id, 1, "Test summary")
    
    # Удаляем задачу
    success = task_service.delete_task(task_id)
    
    assert success is True
    
    # Проверяем, что задача удалена
    task_data = task_service.get_task(task_id)
    assert task_data is None


def test_save_summary_nonexistent_task(task_service):
    """Тест сохранения summary для несуществующей задачи"""
    success = task_service.save_summary(999, 1, "Test summary")
    
    assert success is False


def test_update_task_status(task_service):
    """Тест обновления статуса задачи"""
    # Создаем задачу
    task_id = task_service.create_task("Test Task")
    
    # Проверяем начальный статус
    task_data = task_service.get_task(task_id)
    assert task_data["status"] == "open"
    
    # Обновляем статус на "completed"
    success = task_service.update_task_status(task_id, "completed")
    
    assert success is True
    
    # Проверяем обновление
    task_data = task_service.get_task(task_id)
    assert task_data["status"] == "completed"
    
    # Возвращаем статус на "open"
    success = task_service.update_task_status(task_id, "open")
    
    assert success is True
    
    # Проверяем обновление
    task_data = task_service.get_task(task_id)
    assert task_data["status"] == "open"


def test_update_task_status_invalid(task_service):
    """Тест обновления статуса задачи с невалидными данными"""
    # Создаем задачу
    task_id = task_service.create_task("Test Task")
    
    # Пробуем установить невалидный статус
    success = task_service.update_task_status(task_id, "invalid")
    
    assert success is False
    
    # Пробуем обновить статус несуществующей задачи
    success = task_service.update_task_status(999, "completed")
    
    assert success is False


def test_list_tasks_with_status_filter(task_service):
    """Тест фильтрации задач по статусу"""
    # Создаем задачи с разными статусами
    task_id1 = task_service.create_task("Open Task")
    task_id2 = task_service.create_task("Completed Task")
    
    # Завершаем одну задачу
    task_service.update_task_status(task_id2, "completed")
    
    # Получаем только открытые задачи
    result = task_service.list_tasks(status_filter="open")
    
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["id"] == task_id1
    assert result["tasks"][0]["status"] == "open"
    
    # Получаем только завершенные задачи
    result = task_service.list_tasks(status_filter="completed")
    
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["id"] == task_id2
    assert result["tasks"][0]["status"] == "completed"
    
    # Получаем все задачи
    result = task_service.list_tasks(status_filter=None)
    assert len(result["tasks"]) == 2


def test_list_tasks_pagination(task_service):
    """Тест пагинации списка задач"""
    # Создаем 5 задач
    task_ids = []
    for i in range(5):
        task_id = task_service.create_task(f"Task {i+1}")
        task_ids.append(task_id)
    
    # Получаем первую страницу (2 задачи)
    result = task_service.list_tasks(page=1, page_size=2)
    
    assert len(result["tasks"]) == 2
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["page_size"] == 2
    assert result["pagination"]["total_count"] == 5
    assert result["pagination"]["total_pages"] == 3
    assert result["pagination"]["has_next"] is True
    assert result["pagination"]["has_prev"] is False
    
    # Получаем вторую страницу
    result = task_service.list_tasks(page=2, page_size=2)
    
    assert len(result["tasks"]) == 2
    assert result["pagination"]["has_next"] is True
    assert result["pagination"]["has_prev"] is True
    
    # Получаем третью страницу (последняя)
    result = task_service.list_tasks(page=3, page_size=2)
    
    assert len(result["tasks"]) == 1
    assert result["pagination"]["has_next"] is False
    assert result["pagination"]["has_prev"] is True


def test_list_tasks_sorting(task_service):
    """Тест сортировки списка задач"""
    # Создаем задачи с разными названиями
    task_service.create_task("B Task")
    task_service.create_task("A Task")
    task_service.create_task("C Task")
    
    # Сортировка по названию по возрастанию
    result = task_service.list_tasks(sort_by="title", sort_order="asc")
    
    titles = [task["title"] for task in result["tasks"]]
    assert titles == ["A Task", "B Task", "C Task"]
    
    # Сортировка по названию по убыванию
    result = task_service.list_tasks(sort_by="title", sort_order="desc")
    
    titles = [task["title"] for task in result["tasks"]]
    assert titles == ["C Task", "B Task", "A Task"] 