from typing import List, Optional, Dict, Any

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

try:
    # Для запуска как модуль (pytest, импорт из других модулей)
    from app.models import Task, TaskSummary, DatabaseManager, TaskStatus
except ImportError:
    # Для прямого запуска (fastmcp dev)
    from models import Task, TaskSummary, DatabaseManager, TaskStatus


class TaskService:
    """Сервис для работы с задачами и их summary"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_task(self, title: str, description: Optional[str] = None) -> int:
        """Создает новую задачу и возвращает её ID"""
        with self.db_manager.get_session() as session:
            task = Task(title=title, description=description)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task.id
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получает задачу по ID с её summary"""
        with self.db_manager.get_session() as session:
            task = session.query(Task).options(selectinload(Task.summaries)).filter(Task.id == task_id).first()
            
            if not task:
                return None
            
            return {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "summaries": [
                    {
                        "step_number": summary.step_number,
                        "summary": summary.summary,
                        "created_at": summary.created_at.isoformat()
                    }
                    for summary in sorted(task.summaries, key=lambda x: x.step_number)
                ]
            }
    
    def list_tasks(
        self, 
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Возвращает список задач пользователя с фильтрацией и пагинацией
        
        Args:
            status_filter: Фильтр по статусу ("open", "completed", None для всех)
            page: Номер страницы (начиная с 1)
            page_size: Количество задач на странице
            sort_by: Поле для сортировки ("created_at", "updated_at", "title")
            sort_order: Порядок сортировки ("asc", "desc")
        
        Returns:
            Dict: Список задач с метаданными пагинации
        """
        with self.db_manager.get_session() as session:
            # Базовый запрос
            query = session.query(Task)
            
            # Фильтрация по статусу
            if status_filter:
                if status_filter == "open":
                    query = query.filter(Task.status == TaskStatus.OPEN)
                elif status_filter == "completed":
                    query = query.filter(Task.status == TaskStatus.COMPLETED)
            
            # Подсчет общего количества
            total_count = query.count()
            
            # Сортировка
            sort_column = getattr(Task, sort_by, Task.updated_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            # Пагинация
            offset = (page - 1) * page_size
            tasks = query.offset(offset).limit(page_size).all()
            
            # Подсчет метаданных пагинации
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    }
                    for task in tasks
                ],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
    
    def save_summary(self, task_id: int, step_number: int, summary: str) -> bool:
        """Сохраняет summary для шага задачи"""
        with self.db_manager.get_session() as session:
            # Проверяем, существует ли задача
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return False
            
            # Проверяем, есть ли уже summary для этого шага
            existing_summary = session.query(TaskSummary).filter(
                TaskSummary.task_id == task_id,
                TaskSummary.step_number == step_number
            ).first()
            
            if existing_summary:
                # Обновляем существующий summary
                existing_summary.summary = summary
            else:
                # Создаем новый summary
                task_summary = TaskSummary(
                    task_id=task_id,
                    step_number=step_number,
                    summary=summary
                )
                session.add(task_summary)
            
            # Обновляем время изменения задачи
            task.updated_at = task.updated_at  # Триггер onupdate
            
            session.commit()
            return True
    
    def get_task_context(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает оптимизированный контекст задачи для восстановления"""
        task_data = self.get_task(task_id)
        
        if not task_data:
            return None
        
        # Формируем оптимизированный контекст
        context = {
            "task_id": task_data["id"],
            "title": task_data["title"],
            "description": task_data["description"],
            "total_steps": len(task_data["summaries"]),
            "context_summary": self._build_context_summary(task_data["summaries"]),
            "last_updated": task_data["updated_at"]
        }
        
        return context
    
    def _build_context_summary(self, summaries: List[Dict[str, Any]]) -> str:
        """Строит оптимизированный summary контекста задачи"""
        if not summaries:
            return "Задача только создана, шагов пока нет."
        
        # Группируем summary по шагам
        context_parts = []
        for summary in summaries:
            step_text = f"Шаг {summary['step_number']}: {summary['summary']}"
            context_parts.append(step_text)
        
        return "\n".join(context_parts)
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """Обновляет статус задачи"""
        if status not in ["open", "completed"]:
            return False
            
        with self.db_manager.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return False
            
            if status == "open":
                task.status = TaskStatus.OPEN
            elif status == "completed":
                task.status = TaskStatus.COMPLETED
            
            session.commit()
            return True
    
    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу и все её summary"""
        with self.db_manager.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return False
            
            session.delete(task)
            session.commit()
            return True 