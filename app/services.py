from typing import List, Optional, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

try:
    # Для запуска как модуль (pytest, импорт из других модулей)
    from app.models import Task, TaskSummary, DatabaseManager
except ImportError:
    # Для прямого запуска (fastmcp dev)
    from models import Task, TaskSummary, DatabaseManager


class TaskService:
    """Сервис для работы с задачами и их summary"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_task(self, title: str, description: Optional[str] = None) -> int:
        """Создает новую задачу и возвращает её ID"""
        async with self.db_manager.get_session() as session:
            task = Task(title=title, description=description)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task.id
    
    async def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получает задачу по ID с её summary"""
        async with self.db_manager.get_session() as session:
            stmt = select(Task).options(selectinload(Task.summaries)).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            return {
                "id": task.id,
                "title": task.title,
                "description": task.description,
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
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """Возвращает список всех задач"""
        async with self.db_manager.get_session() as session:
            stmt = select(Task).order_by(desc(Task.updated_at))
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            
            return [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                }
                for task in tasks
            ]
    
    async def save_summary(self, task_id: int, step_number: int, summary: str) -> bool:
        """Сохраняет summary для шага задачи"""
        async with self.db_manager.get_session() as session:
            # Проверяем, существует ли задача
            task_stmt = select(Task).where(Task.id == task_id)
            task_result = await session.execute(task_stmt)
            task = task_result.scalar_one_or_none()
            
            if not task:
                return False
            
            # Проверяем, есть ли уже summary для этого шага
            summary_stmt = select(TaskSummary).where(
                TaskSummary.task_id == task_id,
                TaskSummary.step_number == step_number
            )
            summary_result = await session.execute(summary_stmt)
            existing_summary = summary_result.scalar_one_or_none()
            
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
            
            await session.commit()
            return True
    
    async def get_task_context(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает оптимизированный контекст задачи для восстановления"""
        task_data = await self.get_task(task_id)
        
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
        
        context_parts = []
        for summary_data in summaries:
            step_num = summary_data["step_number"]
            summary_text = summary_data["summary"]
            context_parts.append(f"Шаг {step_num}: {summary_text}")
        
        return "\n".join(context_parts)
    
    async def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу и все её summary"""
        async with self.db_manager.get_session() as session:
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                return False
            
            await session.delete(task)
            await session.commit()
            return True 