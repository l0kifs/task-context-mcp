import asyncio
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

try:
    # Для запуска как модуль (pytest, импорт из других модулей)
    from app.models import DatabaseManager
    from app.services import TaskService
except ImportError:
    # Для прямого запуска (fastmcp dev)
    from models import DatabaseManager
    from services import TaskService


# Pydantic модели для валидации входных данных
class CreateTaskRequest(BaseModel):
    title: str = Field(..., description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")


class SaveSummaryRequest(BaseModel):
    task_id: int = Field(..., description="ID задачи")
    step_number: int = Field(..., description="Номер шага")
    summary: str = Field(..., description="Summary шага")


class GetTaskContextRequest(BaseModel):
    task_id: int = Field(..., description="ID задачи")


class DeleteTaskRequest(BaseModel):
    task_id: int = Field(..., description="ID задачи для удаления")


class UpdateTaskStatusRequest(BaseModel):
    task_id: int = Field(..., description="ID задачи")
    status: str = Field(..., description="Новый статус задачи", pattern="^(open|completed)$")


class ListTasksRequest(BaseModel):
    status_filter: Optional[str] = Field(None, description="Фильтр по статусу", pattern="^(open|completed)$")
    page: int = Field(1, description="Номер страницы", ge=1)
    page_size: int = Field(10, description="Размер страницы", ge=1, le=100)
    sort_by: str = Field("updated_at", description="Поле для сортировки", pattern="^(created_at|updated_at|title)$")
    sort_order: str = Field("desc", description="Порядок сортировки", pattern="^(asc|desc)$")


# Инициализация MCP сервера
mcp = FastMCP("Task Context Server")

# Глобальные переменные для БД и сервиса
db_manager: Optional[DatabaseManager] = None
task_service: Optional[TaskService] = None


async def initialize_database():
    """Инициализация базы данных"""
    global db_manager, task_service
    
    db_manager = DatabaseManager()
    await db_manager.create_tables()
    task_service = TaskService(db_manager)


@mcp.tool()
async def create_task(request: CreateTaskRequest) -> Dict[str, Any]:
    """
    Создает новую задачу и возвращает её ID.
    
    Args:
        request (CreateTaskRequest): Данные для создания задачи
            - title (str): Название задачи. Обязательное поле. 
              Примеры: "Разработка веб-приложения", "Анализ данных", "Создание API"
            - description (str, optional): Подробное описание задачи. Может быть None.
              Примеры: "Создание REST API на FastAPI с аутентификацией", 
              "Анализ продаж за последний квартал с визуализацией"
    
    Returns:
        Dict[str, Any]: Результат операции
            - success (bool): True если задача создана успешно, False при ошибке
            - task_id (int): Уникальный идентификатор созданной задачи (только при success=True)
            - message (str): Описание результата операции
            - error (str): Описание ошибки (только при success=False)
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        task_id = await task_service.create_task(
            title=request.title,
            description=request.description
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Задача '{request.title}' создана с ID {task_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при создании задачи: {str(e)}"
        }


@mcp.tool()
async def save_summary(request: SaveSummaryRequest) -> Dict[str, Any]:
    """
    Сохраняет summary для шага задачи.
    
    Args:
        request (SaveSummaryRequest): Данные summary для сохранения
            - task_id (int): Уникальный идентификатор задачи. Должен существовать в БД.
              Примеры: 1, 42, 123
            - step_number (int): Номер шага в задаче. Положительное число.
              Примеры: 1, 2, 3, 10. Если шаг уже существует, summary будет обновлен
            - summary (str): Текст summary шага. Рекомендуется до 200 слов.
              Структура: "Выполнено: [описание]\nРезультат: [что получилось]\nПроблемы: [если были]\nДалее: [следующий шаг]"
              Пример: "Выполнено: Создание моделей БД\nРезультат: Готовые модели Task и TaskSummary\nПроблемы: нет\nДалее: Реализация API"
    
    Returns:
        Dict[str, Any]: Результат операции
            - success (bool): True если summary сохранен успешно, False при ошибке
            - message (str): Описание результата операции
            - error (str): Описание ошибки (только при success=False)
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        success = await task_service.save_summary(
            task_id=request.task_id,
            step_number=request.step_number,
            summary=request.summary
        )
        
        if success:
            return {
                "success": True,
                "message": f"Summary для шага {request.step_number} задачи {request.task_id} сохранен"
            }
        else:
            return {
                "success": False,
                "error": f"Задача с ID {request.task_id} не найдена"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при сохранении summary: {str(e)}"
        }


@mcp.tool()
async def get_task_context(request: GetTaskContextRequest) -> Dict[str, Any]:
    """
    Возвращает оптимизированный контекст задачи для восстановления.
    
    Args:
        request (GetTaskContextRequest): Запрос на получение контекста
            - task_id (int): Уникальный идентификатор задачи. Должен существовать в БД.
              Примеры: 1, 42, 123
    
    Returns:
        Dict[str, Any]: Результат операции
            При success=True:
            - success (bool): True если контекст получен успешно
            - context (Dict): Контекст задачи
                - task_id (int): ID задачи
                - title (str): Название задачи
                - description (str): Описание задачи
                - total_steps (int): Общее количество шагов
                - context_summary (str): Сжатый summary всех шагов
                - last_updated (str): Время последнего обновления в ISO формате
            При success=False:
            - success (bool): False при ошибке
            - error (str): Описание ошибки
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        context = await task_service.get_task_context(request.task_id)
        
        if context:
            return {
                "success": True,
                "context": context
            }
        else:
            return {
                "success": False,
                "error": f"Задача с ID {request.task_id} не найдена"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при получении контекста: {str(e)}"
        }


@mcp.tool()
async def list_tasks(request: Optional[ListTasksRequest] = None) -> Dict[str, Any]:
    """
    Возвращает список задач пользователя с фильтрацией и пагинацией.
    
    Args:
        request (ListTasksRequest, optional): Параметры запроса
            - status_filter (str, optional): Фильтр по статусу
              Возможные значения: "open", "completed", None (все задачи)
              Примеры: "open" - только открытые, "completed" - только завершенные
            - page (int): Номер страницы (начиная с 1). По умолчанию: 1
              Примеры: 1, 2, 3
            - page_size (int): Количество задач на странице (1-100). По умолчанию: 10
              Примеры: 5, 10, 20, 50
            - sort_by (str): Поле для сортировки. По умолчанию: "updated_at"
              Возможные значения: "created_at", "updated_at", "title"
            - sort_order (str): Порядок сортировки. По умолчанию: "desc"
              Возможные значения: "asc" (по возрастанию), "desc" (по убыванию)
    
    Returns:
        Dict[str, Any]: Результат операции
            При success=True:
            - success (bool): True если список получен успешно
            - tasks (List[Dict]): Список задач согласно фильтрам и сортировке
                Каждая задача содержит:
                - id (int): Уникальный идентификатор задачи
                - title (str): Название задачи
                - description (str): Описание задачи
                - status (str): Статус задачи ("open" или "completed")
                - created_at (str): Время создания в ISO формате
                - updated_at (str): Время последнего обновления в ISO формате
            - pagination (Dict): Метаданные пагинации
                - page (int): Текущая страница
                - page_size (int): Размер страницы
                - total_count (int): Общее количество задач (с учетом фильтра)
                - total_pages (int): Общее количество страниц
                - has_next (bool): Есть ли следующая страница
                - has_prev (bool): Есть ли предыдущая страница
            При success=False:
            - success (bool): False при ошибке
            - error (str): Описание ошибки
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        # Устанавливаем значения по умолчанию, если request не передан
        if request is None:
            request = ListTasksRequest()
        
        result = await task_service.list_tasks(
            status_filter=request.status_filter,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )
        
        return {
            "success": True,
            **result  # Распаковываем tasks и pagination
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при получении списка задач: {str(e)}"
        }


@mcp.tool()
async def update_task_status(request: UpdateTaskStatusRequest) -> Dict[str, Any]:
    """
    Обновляет статус задачи (открыта/завершена).
    
    Args:
        request (UpdateTaskStatusRequest): Запрос на обновление статуса
            - task_id (int): Уникальный идентификатор задачи. Должен существовать в БД.
              Примеры: 1, 42, 123
            - status (str): Новый статус задачи. Обязательное поле.
              Возможные значения: "open" (открыта), "completed" (завершена)
              Примеры: "completed" - для завершения задачи, "open" - для переоткрытия
    
    Returns:
        Dict[str, Any]: Результат операции
            При success=True:
            - success (bool): True если статус обновлен успешно
            - message (str): Подтверждение обновления с указанием нового статуса
            При success=False:
            - success (bool): False при ошибке
            - error (str): Описание ошибки (например, "Задача с ID X не найдена")
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        success = await task_service.update_task_status(request.task_id, request.status)
        
        if success:
            status_text = "завершена" if request.status == "completed" else "открыта"
            return {
                "success": True,
                "message": f"Статус задачи {request.task_id} изменен на '{status_text}'"
            }
        else:
            return {
                "success": False,
                "error": f"Задача с ID {request.task_id} не найдена"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при обновлении статуса: {str(e)}"
        }


@mcp.tool()
async def delete_task(request: DeleteTaskRequest) -> Dict[str, Any]:
    """
    Удаляет задачу и все её summary.
    
    Args:
        request (DeleteTaskRequest): Запрос на удаление задачи
            - task_id (int): Уникальный идентификатор задачи для удаления. Должен существовать в БД.
              Примеры: 1, 42, 123
              ВНИМАНИЕ: Операция необратима! Будут удалены задача и все связанные summary.
    
    Returns:
        Dict[str, Any]: Результат операции
            При success=True:
            - success (bool): True если задача удалена успешно
            - message (str): Подтверждение удаления с указанием ID задачи
            При success=False:
            - success (bool): False при ошибке
            - error (str): Описание ошибки (например, "Задача с ID X не найдена")
    """
    if not task_service:
        return {"error": "Database not initialized"}
    
    try:
        success = await task_service.delete_task(request.task_id)
        
        if success:
            return {
                "success": True,
                "message": f"Задача {request.task_id} удалена"
            }
        else:
            return {
                "success": False,
                "error": f"Задача с ID {request.task_id} не найдена"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при удалении задачи: {str(e)}"
        }


@mcp.resource("agent://workflow_rules")
async def get_agent_workflow_rules() -> str:
    """
    Возвращает общие правила работы агента с MCP инструментами.
    
    Args:
        Нет параметров
    
    Returns:
        str: Подробные правила использования MCP инструментов в формате Markdown
            Включает:
            - Когда создавать новые задачи
            - Как правильно сохранять summary шагов
            - Стратегии восстановления контекста
            - Принципы управления задачами
            - Рекомендации по оптимизации workflow
    """
    return """
# Правила работы AI-агента с Task Context MCP

## Общие принципы

### 1. Контекстная осведомленность
- **Всегда** проверяй наличие активных задач перед началом работы
- Используй `list_tasks` для получения обзора текущих задач
- Восстанавливай контекст через `get_task_context` при продолжении работы

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
Выполнено: [что сделано]
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
- Summary: "Выполнено: Создание моделей БД. Результат: 5 моделей с связями. Проблемы: нет. Далее: API endpoints"
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
    
    Args:
        Нет параметров
    
    Returns:
        str: Подробные правила оптимизации summary в формате Markdown
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
Проблемы: [если были, кратко]
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


def main():
    """Основная функция для запуска сервера"""
    print("Запуск Task Context MCP Server...")
    
    async def setup_and_run():
        try:
            # Инициализируем базу данных
            await initialize_database()
            print("База данных инициализирована")
            print("MCP сервер готов к работе")
        except Exception as e:
            print(f"Ошибка при инициализации: {e}")
            raise
    
    # Инициализируем базу данных при старте
    asyncio.run(setup_and_run())
    
    # Запускаем сервер (FastMCP сам управляет event loop)
    mcp.run()


if __name__ == "__main__":
    main()
