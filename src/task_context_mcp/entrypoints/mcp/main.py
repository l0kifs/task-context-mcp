"""MCP server entrypoint for Task Context MCP."""

import asyncio
from typing import Any

from fastmcp import FastMCP

from task_context_mcp.business.services import TaskService
from task_context_mcp.config.logging_config import setup_logging
from task_context_mcp.integrations.database.manager import DatabaseManager
from task_context_mcp.integrations.database.repositories import (
    TaskRepositoryImpl,
    TaskSummaryRepositoryImpl,
)

# Global variables for dependency injection
db_manager: DatabaseManager | None = None
task_service: TaskService | None = None


async def initialize_dependencies() -> None:
    """Initialize all dependencies for the MCP server."""
    global db_manager, task_service

    # Set up logging
    setup_logging()

    # Initialize database
    db_manager = DatabaseManager()
    await db_manager.initialize()

    # Create repositories
    session = db_manager.get_session()
    task_repo = TaskRepositoryImpl(session)
    summary_repo = TaskSummaryRepositoryImpl(session)

    # Create services
    task_service = TaskService(task_repo, summary_repo)


# Initialize MCP server
mcp = FastMCP(name="Task Context Server")


@mcp.tool()
async def create_task(title: str, description: str | None = None) -> dict[str, Any]:
    """
    Создает новую задачу и возвращает её ID.

    Эта функция позволяет AI-агенту создавать новые задачи для отслеживания
    прогресса работы и сохранения контекста между сессиями.

    Args:
        title: Название задачи (обязательно, 1-255 символов)
        description: Описание задачи (опционально, до 1000 символов)

    Returns:
        Dict с результатом операции:
            - success: True при успешном создании
            - task_id: ID созданной задачи
            - message: Описание результата
            - error: Описание ошибки (только при success=False)
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        task_id = await task_service.create_task(title=title, description=description)

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Задача '{title}' создана с ID {task_id}",
        }
    except ValueError as e:
        return {"success": False, "error": f"Ошибка валидации: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка при создании задачи: {e!s}"}


@mcp.tool()
async def save_summary(task_id: int, step_number: int, summary: str) -> dict[str, Any]:
    """
    Сохраняет summary для шага задачи.

    Позволяет агенту сохранять прогресс работы по шагам для последующего
    восстановления контекста. Если summary для шага уже существует, он обновляется.

    Args:
        task_id: ID задачи (обязательно, положительное число)
        step_number: Номер шага (обязательно, положительное число)
        summary: Текст summary (обязательно, 1-5000 символов)

    Returns:
        Dict с результатом операции:
            - success: True при успешном сохранении
            - message: Описание результата
            - error: Описание ошибки (только при success=False)
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        success = await task_service.save_summary(
            task_id=task_id,
            step_number=step_number,
            summary=summary,
        )

        if success:
            return {
                "success": True,
                "message": f"Summary для шага {step_number} задачи {task_id} сохранен",
            }
        return {"success": False, "error": f"Задача с ID {task_id} не найдена"}
    except ValueError as e:
        return {"success": False, "error": f"Ошибка валидации: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка при сохранении summary: {e!s}"}


@mcp.tool()
async def get_task_context(task_id: int) -> dict[str, Any]:
    """
    Возвращает оптимизированный контекст задачи для восстановления.

    Предоставляет агенту сжатый контекст задачи, оптимизированный для
    минимизации использования токенов при сохранении всей необходимой информации.

    Args:
        task_id: ID задачи (обязательно, положительное число)

    Returns:
        Dict с результатом операции:
            При success=True:
            - success: True при успешном получении
            - context: Контекст задачи
                - task_id: ID задачи
                - title: Название задачи
                - description: Описание задачи
                - total_steps: Общее количество шагов
                - context_summary: Сжатый summary всех шагов
                - last_updated: Время последнего обновления в ISO формате
            При success=False:
            - success: False при ошибке
            - error: Описание ошибки
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        context = await task_service.get_task_context(task_id)

        if context:
            return {
                "success": True,
                "context": {
                    "task_id": context.task_id,
                    "title": context.title,
                    "description": context.description,
                    "total_steps": context.total_steps,
                    "context_summary": context.context_summary,
                    "last_updated": context.last_updated,
                },
            }
        return {"success": False, "error": f"Задача с ID {task_id} не найдена"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка при получении контекста: {e!s}"}


@mcp.tool()
async def list_tasks(
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """
    Возвращает список задач пользователя с фильтрацией и пагинацией.

    Позволяет агенту просматривать существующие задачи, фильтровать их
    по статусу и сортировать для эффективного управления рабочим процессом.

    Args:
        status_filter: Фильтр по статусу ("open", "completed", null для всех)
        page: Номер страницы (по умолчанию: 1)
        page_size: Размер страницы (по умолчанию: 10, максимум: 100)
        sort_by: Поле сортировки ("created_at", "updated_at", "title")
        sort_order: Порядок сортировки ("asc", "desc")

    Returns:
        Dict с результатом операции:
            При success=True:
            - success: True при успешном получении списка
            - tasks: Список задач с их атрибутами
            - pagination: Метаданные пагинации
                - page: Текущая страница
                - page_size: Размер страницы
                - total_count: Общее количество задач
                - total_pages: Общее количество страниц
                - has_next: Есть ли следующая страница
                - has_prev: Есть ли предыдущая страница
            При success=False:
            - success: False при ошибке
            - error: Описание ошибки
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        result = await task_service.list_tasks(
            status_filter=status_filter,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Преобразуем результат в словарь
        tasks_data = []
        for task in result.tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            tasks_data.append(task_dict)

        return {
            "success": True,
            "tasks": tasks_data,
            "pagination": {
                "page": result.pagination.page,
                "page_size": result.pagination.page_size,
                "total_count": result.pagination.total_count,
                "total_pages": result.pagination.total_pages,
                "has_next": result.pagination.has_next,
                "has_prev": result.pagination.has_prev,
            },
        }
    except Exception as e:
        return {"success": False, "error": f"Ошибка при получении списка задач: {e!s}"}


@mcp.tool()
async def update_task_status(task_id: int, status: str) -> dict[str, Any]:
    """
    Обновляет статус задачи (открыта/завершена).

    Позволяет агенту изменять статус задач для отражения текущего
    состояния работы.

    Args:
        task_id: ID задачи (обязательно, положительное число)
        status: Новый статус ("open" или "completed")

    Returns:
        Dict с результатом операции:
            При success=True:
            - success: True при успешном обновлении
            - message: Подтверждение изменения статуса
            При success=False:
            - success: False при ошибке
            - error: Описание ошибки
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        success = await task_service.update_task_status(task_id, status)

        if success:
            status_text = "завершена" if status == "completed" else "открыта"
            return {
                "success": True,
                "message": f"Статус задачи {task_id} изменен на '{status_text}'",
            }
        return {"success": False, "error": f"Задача с ID {task_id} не найдена"}
    except ValueError as e:
        return {"success": False, "error": f"Ошибка валидации: {e!s}"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка при обновлении статуса: {e!s}"}


@mcp.tool()
async def delete_task(task_id: int) -> dict[str, Any]:
    """
    Удаляет задачу и все её summary.

    Полностью удаляет задачу и все связанные с ней данные.
    Эта операция необратима.

    Args:
        task_id: ID задачи для удаления (обязательно, положительное число)

    Returns:
        Dict с результатом операции:
            При success=True:
            - success: True при успешном удалении
            - message: Подтверждение удаления
            При success=False:
            - success: False при ошибке
            - error: Описание ошибки
    """
    if not task_service:
        return {"success": False, "error": "Сервис не инициализирован"}

    try:
        success = await task_service.delete_task(task_id)

        if success:
            return {"success": True, "message": f"Задача {task_id} удалена"}
        return {"success": False, "error": f"Задача с ID {task_id} не найдена"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка при удалении задачи: {e!s}"}


@mcp.resource("agent://workflow_rules")
async def get_agent_workflow_rules() -> str:
    """
    Возвращает общие правила работы агента с MCP инструментами.

    Resource содержит подробные рекомендации по использованию инструментов
    для эффективного управления задачами и сохранения контекста.
    """
    return """
# Правила работы AI-агента с Task Context MCP

## Общие принципы

### 1. Контекстная осведомленность
- **Всегда** проверяй наличие активных задач перед началом работы
- Используй `list_tasks` для получения обзора текущих задач
- Восстанавливай контекст через `get_task_context` при переходе в новый чат

### 2. Проактивное управление задачами
- Создавай новую задачу (`create_task`) для каждого значимого проекта или запроса
- Не создавай задачи для простых вопросов, требующих одного ответа
- Группируй связанные активности в рамках одной задачи

## Когда использовать инструменты

### `create_task` - Создание задачи
**Используй когда:**
- Пользователь начинает новый проект или сложную задачу
- Работа потребует несколько шагов или сессий
- Нужно отслеживать прогресс выполнения
- Задача может быть прервана и продолжена позже

**Примеры:**
- "Разработай веб-приложение"
- "Проанализируй данные продаж"
- "Создай план маркетинговой кампании"

**НЕ используй для:**
- Простых вопросов ("Что такое Python?")
- Одноразовых запросов
- Исправления ошибок в коде

### `save_summary` - Сохранение прогресса
**Используй после каждого значимого шага:**
- Завершения этапа работы
- Решения проблемы
- Принятия важного решения
- Достижения промежуточного результата

**Структура summary:**
```
Выполнено: [краткое описание]
Результат: [что получилось]
Проблемы: [если были]
Далее: [следующий шаг]
```

**Частота сохранения:**
- После каждых 10-15 минут активной работы
- При смене направления работы
- Перед переходом к новому компоненту/модулю
- При обнаружении и решении проблем

### `get_task_context` - Восстановление контекста
**Используй когда:**
- Пользователь возвращается к прерванной задаче
- Нужно вспомнить, что было сделано ранее
- Требуется оценить текущий прогресс
- Планируешь следующие шаги

**После восстановления:**
- Кратко резюмируй текущее состояние
- Предложи варианты продолжения
- Уточни приоритеты у пользователя

### `list_tasks` - Обзор задач
**Используй для:**
- Показа активных проектов пользователю
- Выбора задачи для продолжения работы
- Оценки общей загрузки
- Планирования приоритетов

**Параметры фильтрации:**
- `status_filter`: "open" (только активные), "completed" (только завершенные), null (все)
- `page`, `page_size`: для пагинации больших списков
- `sort_by`: "updated_at" (по обновлению), "created_at" (по созданию), "title" (по названию)
- `sort_order`: "desc" (новые первые), "asc" (старые первые)

**Рекомендации:**
- По умолчанию показывай только открытые задачи
- Используй пагинацию при большом количестве задач
- Сортируй по времени обновления для актуальности

### `update_task_status` - Изменение статуса задачи
**Используй когда:**
- Задача завершена полностью (status="completed")
- Нужно переоткрыть завершенную задачу (status="open")
- Пользователь явно просит изменить статус

**Статусы:**
- "open" - задача активна, работа продолжается
- "completed" - задача завершена, цель достигнута

### `delete_task` - Удаление задач
**Используй только когда:**
- Пользователь явно просит удалить задачу
- Задача отменена или больше не актуальна
- Задача была создана по ошибке

**ВНИМАНИЕ:** Операция необратима! Рекомендуется использовать `update_task_status` с "completed" вместо удаления.

## Стратегии работы

### Начало сессии
1. Поприветствуй пользователя
2. Выполни `list_tasks` для обзора
3. Если есть активные задачи - предложи продолжить
4. Если новый запрос - оцени нужность создания задачи

### Во время работы
1. Сохраняй прогресс регулярно через `save_summary`
2. Фокусируйся на результатах, а не на процессе
3. Документируй важные решения и их обоснования
4. Отмечай проблемы и способы их решения

### Завершение работы
1. Сохрани финальный summary с результатами
2. Укажи статус задачи (завершена/приостановлена)
3. Опиши следующие шаги, если задача не завершена
4. Предложи пользователю план дальнейших действий

## Оптимизация производительности

### Минимизация токенов
- Используй сжатые summary (до 200 слов)
- Избегай дублирования информации
- Фокусируйся на ключевых результатах
- Используй техническую терминологию без лишних объяснений

### Управление контекстом
- Регулярно "сбрасывай" старый контекст через summary
- Восстанавливай только необходимую информацию
- Группируй связанные шаги в логические блоки

### Эффективное планирование
- Разбивай большие задачи на этапы
- Устанавливай четкие критерии завершения шагов
- Планируй проверочные точки для оценки прогресса

## Обработка ошибок

### При сбоях инструментов
- Информируй пользователя о проблеме
- Предложи альтернативные способы продолжения
- Сохрани текущий прогресс перед повторными попытками

### При потере контекста
- Используй `get_task_context` для восстановления
- Попроси пользователя уточнить текущие цели
- Начни с краткого резюме понимания ситуации

## Примеры хороших практик

### ✅ Хорошо:
- Создание задачи "Разработка API для интернет-магазина"
- Summary: "Выполнено: Создание моделей БД. Результат: Готовые модели с связями. Проблемы: нет. Далее: API endpoints"
- Восстановление контекста перед продолжением работы

### ❌ Плохо:
- Создание задачи для вопроса "Как работает HTTP?"
- Summary: "Я долго думал о том, как лучше реализовать функцию, потом решил использовать SQLAlchemy..."
- Работа без сохранения прогресса

Помни: MCP инструменты - это твоя "внешняя память". Используй их для создания непрерывного, эффективного опыта работы с пользователем.
"""


@mcp.resource("summary://compression_rules")
async def get_compression_rules() -> str:
    """
    Возвращает правила для оптимизации summary агентом.

    Resource содержит рекомендации по сжатию summary для
    эффективного использования токенов.
    """
    return """
# Правила оптимизации Summary для AI-агента

## Цель
Создавать краткие, но информативные summary каждого шага задачи для минимизации токенов при сохранении качества контекста.

## Принципы сжатия

1. **Фокус на результате**: Описывайте что было достигнуто, а не как.
2. **Ключевые решения**: Сохраняйте важные технические решения и их обоснования.
3. **Проблемы и их решения**: Кратко фиксируйте встреченные проблемы и способы их решения.
4. **Следующие шаги**: Указывайте что планируется делать дальше.

## Структура summary (рекомендуемая)
```
Выполнено: [краткое описание]
Результат: [что получилось]
Проблемы: [если были]
Далее: [следующий шаг]
```

## Ограничения
- Максимум 200 слов на summary
- Избегайте повторения информации из предыдущих шагов
- Используйте технические термины без лишних объяснений
- Сохраняйте только критически важную информацию

## Примеры

❌ Плохо:
"Я начал работать над созданием базы данных. Сначала я изучил требования, потом выбрал SQLAlchemy как ORM, потом создал модели для таблиц tasks и task_summaries. В модели Task я добавил поля id, title, description, created_at, updated_at. В модели TaskSummary добавил поля id, task_id, step_number, summary, created_at. Также настроил связи между таблицами."

✅ Хорошо:
"Выполнено: Создание моделей БД (Task, TaskSummary) с SQLAlchemy
Результат: Готовые модели с связями, поддержка async операций
Проблемы: нет
Далее: Реализация сервисного слоя"
"""


async def main():
    """Main entry point for the MCP server."""
    try:
        # Initialize dependencies
        await initialize_dependencies()

        # Run MCP server
        await mcp.run_async()

    except Exception:
        # Log error and re-raise
        if db_manager:
            await db_manager.close()
        raise
    finally:
        # Ensure database connections are closed
        if db_manager:
            await db_manager.close()


def run():
    """Synchronous entry point for the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    # Run the server
    run()
