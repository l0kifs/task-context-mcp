# Task Context MCP Server

MCP (Model Context Protocol) сервер для сохранения и восстановления контекста задач AI-агента. Позволяет агенту сохранять summary каждого шага задачи в базе данных и быстро восстанавливать контекст при переходе в новый чат.

## Возможности

- ✅ Создание и управление задачами
- ✅ Сохранение summary для каждого шага задачи
- ✅ Быстрое восстановление контекста задачи
- ✅ Оптимизация summary для минимизации токенов
- ✅ Асинхронная работа с базой данных SQLite
- ✅ Полная совместимость с MCP протоколом

## Установка и запуск

### Требования

- Python 3.11+
- uv (менеджер пакетов)

### Установка

1. Клонируйте репозиторий:

```bash
git clone <repository-url>
cd task-context-mcp
```

2. Установите зависимости:

```bash
uv sync
```

3. Запустите сервер:

```bash
uv run python -m app.server
```

Сервер будет доступен по умолчанию на порту, который выберет FastMCP.

## Использование

### MCP Tools (Инструменты)

Сервер предоставляет следующие инструменты для AI-агента:

#### 1. `create_task`

Создает новую задачу.

**Параметры:**

- `title` (str): Название задачи
- `description` (str, optional): Описание задачи

**Возвращает:**

```json
{
  "success": true,
  "task_id": 1,
  "message": "Задача 'Создание MCP сервера' создана с ID 1"
}
```

#### 2. `save_summary`

Сохраняет summary для шага задачи.

**Параметры:**

- `task_id` (int): ID задачи
- `step_number` (int): Номер шага
- `summary` (str): Текст summary

**Возвращает:**

```json
{
  "success": true,
  "message": "Summary для шага 1 задачи 1 сохранен"
}
```

#### 3. `get_task_context`

Возвращает оптимизированный контекст задачи.

**Параметры:**

- `task_id` (int): ID задачи

**Возвращает:**

```json
{
  "success": true,
  "context": {
    "task_id": 1,
    "title": "Создание MCP сервера",
    "description": "Разработка сервера для сохранения контекста",
    "total_steps": 3,
    "context_summary": "Шаг 1: Создание моделей БД\nШаг 2: Реализация сервиса\nШаг 3: Создание MCP сервера",
    "last_updated": "2024-01-15T10:30:00"
  }
}
```

#### 4. `list_tasks`

Возвращает список задач с фильтрацией и пагинацией.

**Параметры (все опциональные):**

- `status_filter` (str): Фильтр по статусу ("open", "completed", null для всех)
- `page` (int): Номер страницы (по умолчанию: 1)
- `page_size` (int): Размер страницы (по умолчанию: 10, максимум: 100)
- `sort_by` (str): Поле сортировки ("created_at", "updated_at", "title", по умолчанию: "updated_at")
- `sort_order` (str): Порядок сортировки ("asc", "desc", по умолчанию: "desc")

**Возвращает:**

```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "title": "Создание MCP сервера",
      "description": "Разработка сервера для сохранения контекста",
      "status": "open",
      "created_at": "2024-01-15T09:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

#### 5. `update_task_status`

Обновляет статус задачи (открыта/завершена).

**Параметры:**

- `task_id` (int): ID задачи
- `status` (str): Новый статус ("open" или "completed")

**Возвращает:**

```json
{
  "success": true,
  "message": "Статус задачи 1 изменен на 'завершена'"
}
```

#### 6. `delete_task`

Удаляет задачу и все её summary.

**Параметры:**

- `task_id` (int): ID задачи

**Возвращает:**

```json
{
  "success": true,
  "message": "Задача 1 удалена"
}
```

### MCP Resources (Ресурсы)

#### `agent://workflow_rules`

Возвращает общие правила работы AI-агента с MCP инструментами:

- Когда создавать новые задачи
- Как правильно сохранять summary шагов  
- Стратегии восстановления контекста
- Принципы управления задачами
- Рекомендации по оптимизации workflow

#### `summary://compression_rules`

Возвращает правила оптимизации summary для агента.

## Структура базы данных

### Таблица `tasks`

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ |
| title | VARCHAR(255) | Название задачи |
| description | TEXT | Описание задачи |
| status | ENUM | Статус задачи ("open", "completed") |
| created_at | DATETIME | Время создания |
| updated_at | DATETIME | Время последнего обновления |

### Таблица `task_summaries`

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ |
| task_id | INTEGER | Внешний ключ на tasks.id |
| step_number | INTEGER | Номер шага |
| summary | TEXT | Текст summary |
| created_at | DATETIME | Время создания |

## Сценарии использования

### 1. Начало новой задачи

```python
# AI-агент создает новую задачу
result = await create_task({
    "title": "Разработка веб-приложения",
    "description": "Создание полнофункционального веб-приложения на FastAPI"
})
task_id = result["task_id"]  # Сохраняем ID для дальнейшего использования
```

### 2. Сохранение прогресса

```python
# После каждого значимого шага агент сохраняет summary
await save_summary({
    "task_id": task_id,
    "step_number": 1,
    "summary": "Выполнено: Настройка проекта и установка зависимостей\nРезультат: Готовая структура проекта с FastAPI\nПроблемы: нет\nДалее: Создание моделей данных"
})

await save_summary({
    "task_id": task_id,
    "step_number": 2,
    "summary": "Выполнено: Создание моделей SQLAlchemy\nРезультат: Модели User, Product, Order\nПроблемы: нет\nДалее: Реализация API endpoints"
})
```

### 3. Восстановление контекста

```python
# В новом чате агент восстанавливает контекст
context = await get_task_context({"task_id": task_id})
print(context["context_summary"])
# Выводит весь прогресс задачи в сжатом виде
```

### 4. Завершение задачи

```python
# Когда задача выполнена, изменяем статус
await update_task_status({
    "task_id": task_id,
    "status": "completed"
})
```

### 5. Просмотр задач с фильтрацией

```python
# Получить только открытые задачи
open_tasks = await list_tasks({
    "status_filter": "open",
    "page": 1,
    "page_size": 10
})

# Получить завершенные задачи, отсортированные по дате создания
completed_tasks = await list_tasks({
    "status_filter": "completed",
    "sort_by": "created_at",
    "sort_order": "desc"
})
```

## Правила оптимизации Summary

Для минимизации токенов при сохранении качества контекста рекомендуется:

### Структура summary

```
Выполнено: [краткое описание]
Результат: [что получилось]
Проблемы: [если были, кратко]
Далее: [следующий шаг]
```

### Принципы

- Максимум 200 слов на summary
- Фокус на результате, а не на процессе
- Сохранение ключевых технических решений
- Избегание повторений из предыдущих шагов

## Тестирование

Запуск тестов:

```bash
# Все тесты
uv run pytest

# Тесты с подробным выводом
uv run pytest -v

# Тесты конкретного модуля
uv run pytest tests/test_services.py
```

## Разработка

### Структура проекта

```
task-context-mcp/
├── app/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy модели
│   ├── services.py        # Бизнес-логика
│   └── server.py          # MCP сервер (точка входа)
├── tests/
│   ├── test_models.py     # Тесты моделей
│   └── test_services.py   # Тесты сервисов
├── docs/
│   └── task-context-mcp-plan.md
├── pyproject.toml         # Конфигурация проекта
└── README.md
```

### Добавление новых функций

1. Обновите модели в `app/models.py`
2. Добавьте бизнес-логику в `app/services.py`
3. Создайте MCP инструменты в `app/server.py`
4. Напишите тесты в `tests/`

## Интеграция с AI-агентами

### Claude Desktop

Добавьте в конфигурацию Claude Desktop:

```json
{
  "mcpServers": {
    "task-context": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.server"],
      "cwd": "/path/to/task-context-mcp"
    }
  }
}
```

### Cursor

Настройте MCP сервер в настройках Cursor, указав путь к исполняемому файлу.

## Лицензия

MIT License

## Поддержка

Для вопросов и предложений создавайте issues в репозитории.
