---
applyTo: '**'
---
# Document Editing Rules

1. Maintain document style and structure — use existing sections and formatting.
2. All edits and additions must be made in logically appropriate sections.
3. Formulate changes concisely, but ensure they are unambiguously clear and preserve the essence.
4. Avoid information duplication — update or expand existing points.
5. Create separate sections for new topics if they don't fit into current ones.
6. All code examples should be minimally necessary for understanding, but fully functional.
7. Maintain consistent terminology, formatting, and language style throughout the document.
8. Make edits with consideration for long-term maintenance and document scalability.

# Python Project Development Rules

Modern rules and best practices for developing Python projects focused on long-term maintenance, readability, and performance.

## Mandatory Tool Requirements

### UV Package Manager - MANDATORY
**CRITICAL REQUIREMENT:** All Python projects MUST exclusively use `uv` as the package manager.

**Forbidden usage:**
- `pip` directly (except for installing UV itself)
- `poetry` 
- `pipenv`
- `conda` for Python dependency management
- `virtualenv` manually

**Required commands for project work:**
- **Project initialization:** `uv init`
- **Dependency installation:** `uv sync`
- **Adding dependencies:** `uv add <package>`
- **Adding dev dependencies:** `uv add --group dev <package>`
- **Running commands:** `uv run <command>`
- **Environment activation:** `uv shell` (when necessary)

**Agent behavior when `uv` is not available in the environment:**
- When executing commands related to dependency management or running tests/scripts, the agent MUST attempt to run them through `uv` by default.
- If `uv` is not found in PATH, the agent MUST attempt to install `uv` automatically by calling the official installation script:
    `curl -LsSf https://astral.sh/uv/install.sh | sh`
- The agent MUST NOT fallback to direct execution of `pytest`, `pip`, or other tools directly without explicit user permission or explicit task specification. In exceptional cases, the agent may suggest a temporary fallback and ask the user, but not take automatic actions that modify the environment without consent.

**Dependency structure:**
- Main dependencies in the `dependencies` section of `pyproject.toml`
- Dependency groups in `[dependency-groups]` for dev/test/lint
- No `requirements.txt` files

**CI/CD setup:**
- UV installation: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Using `uv sync` for dependency installation
- All commands through `uv run`

## Architecture

### Clean Architecture Principles
Adhere to **Clean Architecture** principles with clear layer separation and proper dependency direction:

1. **`src/models/`** - Application models (depend on nothing)
2. **`src/business/`** - Business logic (depends only on models, defines interfaces)
3. **`src/integrations/`** - External system integrations (implement business logic interfaces)
4. **`src/entrypoints/`** - Entry points (compose business logic with integrations)

**Dependency rule:**
- Models → independent
- Business logic → depends on models
- Integrations → **implement interfaces** from business logic (don't depend on it directly)
- Entry points → **compose** business logic with concrete integrations

### Dependency Management
- **Interfaces (`typing.Protocol`)** are defined in business logic
- **Dependency Injection:** Preferably explicit passing through arguments. For complex cases, lightweight DI solutions are acceptable (`dependency-injector`, `punq`)
- **Dependency composition** happens in entry points
- **Configurations:** `pydantic-settings` for typed settings with validation
- **Package manager:** Only `uv` - see "Mandatory Tool Requirements" section

## Project Structure

### Standard Structure (src-layout)
```
project-name/
├── src/
│   └── project_name/
│       ├── __init__.py           # Required for packages
│       ├── config/               # Application configurations
│       │   ├── __init__.py
│       │   ├── settings.py       # Pydantic settings
│       │   └── environments/     # Configs for different environments
│       │       ├── __init__.py
│       │       ├── development.py
│       │       ├── production.py
│       │       └── testing.py
│       ├── models/               # Application models
│       │   ├── __init__.py
│       │   ├── entities.py       # Core entities
│       │   ├── value_objects.py  # Value objects
│       │   └── exceptions.py     # Domain exceptions
│       ├── business/             # Business logic
│       │   ├── __init__.py
│       │   ├── interfaces.py     # Protocol interfaces
│       │   ├── services.py       # Business services
│       │   └── use_cases.py      # Use cases
│       ├── integrations/         # External system integrations
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── repositories.py  # Repository implementations
│       │   │   └── models.py        # ORM models (if used)
│       │   ├── external_apis/
│       │   │   ├── __init__.py
│       │   │   └── clients.py       # HTTP clients
│       │   └── messaging/
│       │       ├── __init__.py
│       │       └── publishers.py   # Event publishing
│       └── entrypoints/          # Application entry points
│           ├── __init__.py
│           ├── cli/              # CLI interface
│           │   ├── __init__.py
│           │   └── commands.py
│           ├── web/              # Web UI (optional)
│           │   ├── __init__.py
│           │   └── app.py
│           └── api/              # HTTP API
│               ├── __init__.py
│               ├── main.py       # FastAPI application
│               ├── routes/
│               ├── schemas.py    # Pydantic schemas for API
│               └── dependencies.py  # DI composition
├── tests/                        # Tests mirror src structure
│   ├── unit/
│   │   ├── test_models/
│   │   ├── test_business/
│   │   └── test_integrations/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── docs/                         # Documentation
├── migrations/                   # Database migrations
├── scripts/                      # Utilities and scripts
├── .github/workflows/            # CI/CD
├── pyproject.toml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile
└── README.md
```

## Layer Implementation

### Configurations (config)
**Purpose:** Typed application settings with validation
- All configurations inherit from `BaseSettings` or `BaseModel`
- Nested configurations — separate models
- Unified environment variable style using prefix and separator
- Validation and properties — through Pydantic

```python
# config/settings.py (minimal example)
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432


class AppSettings(BaseSettings):
    app_name: str = "my-app"
    debug: bool = False
    database: DatabaseSettings = DatabaseSettings()

    # Minimal configuration for loading from .env with prefix
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")


if __name__ == "__main__":
    # Quick example: load settings and print dictionary
    settings = AppSettings()
    print(settings.model_dump())
```

### Models (models)
**Purpose:** Core entities and value objects of the application
- **Entities:** `dataclasses` or `Pydantic` models with identifiers
- **Value objects:** Immutable objects without identifiers
- **Exceptions:** Domain exceptions of the application
- **Dependencies:** No external dependencies

```python
# models/entities.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class User:
    id: UUID
    email: str
    name: str
    is_active: bool = True
```

### Business Logic (business)
**Purpose:** Core application logic and interface definition
- **Interfaces:** Defining contracts for external dependencies
- **Services:** Implementation of business rules
- **Use cases:** Business process orchestration

```python
# business/interfaces.py
from typing import Protocol
from models.entities import User

class UserRepository(Protocol):
    async def save(self, user: User) -> None: ...
    async def get_by_id(self, user_id: UUID) -> Optional[User]: ...

class EmailService(Protocol):
    async def send_welcome_email(self, user: User) -> None: ...

# business/services.py
class UserService:
    def __init__(self, repo: UserRepository, email: EmailService):
        self._repo = repo
        self._email = email
    
    async def register_user(self, email: str, name: str) -> User:
        # Registration business logic
        user = User(id=uuid4(), email=email, name=name)
        await self._repo.save(user)
        await self._email.send_welcome_email(user)
        return user
```

### Integrations (integrations)
**Purpose:** Interface implementations for interacting with external systems
- **Repositories:** Working with databases
- **HTTP clients:** Interaction with external APIs
- **Event publishing:** Message sending

```python
# integrations/database/repositories.py
from business.interfaces import UserRepository
from models.entities import User
from config import settings

class PostgresUserRepository:  # Implements UserRepository
    def __init__(self):
        # Using settings from configuration
        self._connection_string = settings.database.url
    
    async def save(self, user: User) -> None:
        # Implementation for saving to PostgreSQL
        pass
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        # Implementation for retrieving from PostgreSQL
        pass

# integrations/external_apis/clients.py
from business.interfaces import EmailService
from config import settings
import aiosmtplib

class SMTPEmailClient:  # Implements EmailService
    def __init__(self):
        self._smtp_config = settings.email
    
    async def send_welcome_email(self, user: User) -> None:
        # Using SMTP settings
        await aiosmtplib.send(
            message,
            hostname=self._smtp_config.smtp_host,
            port=self._smtp_config.smtp_port,
            username=self._smtp_config.smtp_user,
            password=self._smtp_config.smtp_password,
        )
```

### Entry Points (entrypoints)
**Purpose:** Dependency composition and handling external requests
- **CLI:** Console commands
- **API:** HTTP endpoints
- **Web UI:** Web interface

```python
# entrypoints/api/dependencies.py
from integrations.database.repositories import PostgresUserRepository
from integrations.external_apis.clients import SMTPEmailClient
from business.services import UserService
from config import settings

def create_user_service() -> UserService:
    # Configurations are automatically pulled in integrations
    repo = PostgresUserRepository()
    email_service = SMTPEmailClient()
    return UserService(repo, email_service)

# entrypoints/api/main.py
from fastapi import FastAPI
from config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug
    )
    return app

# entrypoints/api/routes/users.py
@router.post("/users/", response_model=UserResponse)
async def register_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(create_user_service)
):
    user = await user_service.register_user(
        email=user_data.email,
        name=user_data.name
    )
    return UserResponse.from_entity(user)
```

## Code Quality

### Type Annotations and Style
- **Mandatory:** Type annotations everywhere (`mypy --strict`)
- **Formatting:** `ruff format` (Black replacement)
- **Linting:** `ruff check` (flake8, isort, etc. replacement)
- **Pre-commit hooks** for automatic checks

**Naming principles:**
- **Functions and variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Descriptive names:** Avoid placeholder names (`tmp`, `data`, `a`, `b`)

```python
# ✅ Correct
class UserService:
    def create_user_account(self, email: str, name: str) -> User:
        validated_email = self._validate_email_format(email)
        return User(email=validated_email, name=name)

# ❌ Incorrect
class us:  # Unclear name
    def c(self, e, n):  # No types, short names
        tmp = validate(e)  # Placeholder name
        return User(tmp, n)
```

### SOLID Principles
- **SRP:** One class/function = one responsibility
- **OCP:** Extension through new interface implementations
- **LSP:** All interface implementations are interchangeable
- **ISP:** Thin, specialized interfaces
- **DIP:** Dependency on abstractions, inversion through DI

```python
# ✅ Correct: class with single responsibility
class EmailValidator:
    def validate(self, email: str) -> bool:
        return "@" in email and "." in email

class UserRepository:
    def save(self, user: User) -> None:
        # Only saving
        pass

# ❌ Incorrect: monolithic class with multiple responsibilities
class UserManager:
    def validate_email(self, email: str) -> bool: ...
    def send_email(self, email: str, message: str) -> None: ...
    def save_to_db(self, user: User) -> None: ...
    def generate_report(self, users: list[User]) -> str: ...
    def log_activity(self, action: str) -> None: ...
```

### Exception Handling
- **Explicit handling:** Only catch exceptions you can handle correctly
- **Avoid unfiltered `except:`:** Always specify concrete exception types
- **Don't suppress errors silently:** Log context or recreate exception
- **Custom exceptions:** Create domain exceptions for business logic
- **Debug context:** Include sufficient information for diagnostics

```python
# ✅ Correct
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", operation="risky", error=str(e))
    raise BusinessLogicError("Cannot complete user action") from e

# ❌ Incorrect
try:
    result = risky_operation()
except:  # Catching everything
    pass  # Suppressing error without logging
```

## Testing

### Layer-based Testing Strategy
- **Models:** Unit tests for validation and business rules
- **Business logic:** Unit tests with interface mocks (90%+ coverage)
- **Integrations:** Integration tests with real dependencies
- **Entry points:** E2E tests for critical scenarios

### Tools
- **Framework:** `pytest` with plugins (`pytest-asyncio`, `pytest-mock`)
- **Fixtures:** `pytest-factoryboy` for test data
- **Mocks:** `unittest.mock` or `pytest-mock` for interfaces
- **Test configurations:** Separate settings for test environment
- **Property-based tests:** `hypothesis` for complex logic
- **Coverage:** `coverage.py` with reports

### Running Tests
All project tests should be run through `uv`:
```bash
uv run pytest
```

## Project Configuration (pyproject.toml)

### Principles and Requirements
- **Standard:** Strict adherence to [PEP 621](https://peps.python.org/pep-0621/) and [PEP 518](https://peps.python.org/pep-0518/)
- **Package manager:** Configuration for `uv` using specific options
- **Structure:** Logical separation of metadata, dependencies, and tool configuration
- **Validation:** All data should be correctly typed

### Required Sections
1. **`[project]`** - Main project metadata
2. **`[build-system]`** - Build system (for libraries)
3. **`[tool.uv]`** - UV configuration
4. **`[dependency-groups]`** - Development dependency groups

### Minimal pyproject.toml example
```toml
# Required project metadata
[project]
name = "my-project"
version = "0.1.0"
description = "Short project description"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.11.7",
    "loguru>=0.7.0",
]

# Development dependency groups
[dependency-groups]
dev = ["pytest>=8.4.1", "pytest-cov>=6.2.1"]
lint = ["ruff>=0.8.0", "mypy>=1.13.0"]

# Build system (for libraries)
[build-system]
requires = ["uv_build>=0.8.11,<0.9.0"]
build-backend = "uv_build"

# Basic tool configuration
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.mypy]
python_version = "3.12"
strict = true
```

### Key Rules for UV
- **Required fields:** `name`, `version`, `description`, `requires-python`
- **Dependency groups:** Use `[dependency-groups]` for dev/lint/docs dependencies
- **Build system:** `uv_build` for new projects
- **UV sources:** `[tool.uv.sources]` for Git/local/workspace dependencies

## Development Tools

### Project Management
- **Dependencies:** `uv` (mandatory - see section 0)
- **Configuration:** `pyproject.toml` (PEP 621)
- **Automation:** `Makefile` with targets: `install`, `test`, `lint`, `format`, `build`

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml (example)
- Pre-commit hooks
- Ruff linting and formatting  
- MyPy type checking
- Pytest with coverage (by layers)
- Security scan (bandit, safety)
- Integration tests
- Documentation build
```

## Security

### Security Practices
- **Dependency scanning:** `uv tool install safety && uv run safety check` or `uv tool install pip-audit && uv run pip-audit`
- **Code analysis:** `bandit` for vulnerability scanning
- **Secret configuration:** `pydantic-settings` with required secret validation
- **Environment variables:** All secrets only through env variables
- **Input validation:** Pydantic at entry points
- **Authorization:** In business logic, implementation in integrations

```python
# Example of secure configuration
class AppSettings(BaseSettings):
    secret_key: str = Field(..., min_length=32)  # Required and minimum 32 characters
    jwt_secret: str = Field(..., alias="JWT_SECRET_KEY")
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if v == "changeme" or len(set(v)) < 8:
            raise ValueError("Secret key is too weak")
        return v
```

## Logging and Monitoring

### Structured Logging with Loguru
```python
from loguru import logger

# ✅ Correct: structured logging with context
logger.info("User registered", user_id=user.id, email=user.email)
logger.bind(request_id="12345").info("Processing request")

# In business logic
logger.info("User registered", user_id=user.id, email=user.email)

# In integrations
logger.debug("Database query", table="users", operation="insert")

# Contextual logging with additional fields
logger.bind(request_id="12345").info("Processing request")

# ❌ Incorrect: using print for diagnostics
print(f"User {user.id} registered")  # Not structured, not configurable
print("Debug info:", some_variable)  # Will remain in production
```

### Logging Configuration
Use centralized logging configuration:

```python
# config/logging_config.py
import sys
from typing import Optional
from loguru import logger

def logging_config(log_file: Optional[str] = None) -> None:
    """
    Logging configuration.

    Args:
        log_file: Path to log file. If not specified, logging will be console-only.
    """
    # Remove default loguru handler
    logger.remove()

    # Add handler for console output (DEBUG and above)
    logger.add(
        sys.stdout,
        level="DEBUG",
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <white>{message}</white> | {extra}",
    )
    
    if log_file:
        # Add handler for file writing
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
            rotation="10 MB",
            retention=1,
            enqueue=True,
            serialize=False,
        )

# Initialization at entry point
# entrypoints/api/main.py
from config.logging_config import logging_config

def create_app() -> FastAPI:
    # Configure logging on application startup
    logging_config(log_file="logs/app.log" if not settings.debug else None)
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug
    )
    return app
```

### Environment-based Logging Strategy
- **Local:** Colored console output with detailed format
- **Production:** File logging with rotation, structured format
- **Context:** Passing additional fields through `logger.bind()` between layers

## Asynchronous Programming

### Asyncio Strategy
- **Interfaces:** Defined as async in business logic
- **Integrations:** Async implementations for I/O operations
- **Entry points:** Async request handlers
- **CPU-bound tasks:** `concurrent.futures.ProcessPoolExecutor`

## Performance

### Monitoring and Optimization
- **Profiling:** `py-spy` for production, `cProfile` for development
- **Metrics:** At business logic and integration levels
- **Caching:** In integrations, transparent to business logic
- **Connection pools:** In database integrations

## Documentation

### Documentation Standards
- **Architecture:** Dependency diagrams between layers
- **Interfaces:** Detailed contract descriptions
- **API:** Auto-generation from OpenAPI (FastAPI)
- **Business logic:** Docstrings with usage examples

## Versioning and Releases

### Release Process
- **Semantic Versioning:** MAJOR.MINOR.PATCH
- **Migrations:** Interface version compatibility
- **Changelog:** By architecture layers
- **Testing:** Regression tests for all layers

## Makefile (example)

```makefile
.PHONY: install test test-unit test-integration lint format type-check security

install:
	uv sync

test: test-unit test-integration

test-unit:
	uv run pytest tests/unit/ --cov=src/project_name/models --cov=src/project_name/business

test-integration:
	uv run pytest tests/integration/ --cov=src/project_name/integrations

test-e2e:
	uv run pytest tests/e2e/ --cov=src/project_name/entrypoints

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

type-check:
	uv run mypy src

security:
	uv run bandit -r src/
	uv tool install safety && uv run safety check

config-check:
	# Check configuration validity
	python -c "from config import settings; print('✓ Configurations are valid')"

architecture-check:
	# Check architectural principles compliance
	python scripts/check_dependencies.py

all: format lint type-check config-check test security architecture-check
```

---

**Principles:**
1. **Clear separation of responsibilities** between layers
2. **Dependency inversion** through interfaces
3. **Composition at entry points** - the only place for application assembly
4. **Testability** through interface mocking capabilities
5. **Automated checking** of architectural principles

Start simple, increase complexity as needed. Invest in architecture quality from the beginning - it will pay off when scaling.

## Quick Checklist for Quality Python Code

Compact and prioritized set of practices for quick code quality checking in most projects:

### Basics (see "Code Quality" section)
- ✅ Style compliance (PEP 8) and docstrings for public APIs (PEP 257)
- ✅ Small, unambiguous functions and classes (Single Responsibility)
- ✅ Descriptive names (`snake_case` for functions, `PascalCase` for classes)
- ✅ Type annotations and `mypy` integration in CI
- ✅ Automatic formatter and linter (`ruff` and `pre-commit`)

### Reliability (see "Code Quality", "Security" sections)
- ✅ Business logic test coverage (`pytest`) with CI workflow
- ✅ Explicit exception handling (don't use unfiltered `except:`)
- ✅ Structured logging (`loguru`) instead of `print`
- ✅ Centralized configuration (`pydantic-settings`) and secrets through environment

### Architecture (see "Architecture" section)
- ✅ Layer separation: models, business logic, integrations, entry points
- ✅ External dependency mocking in unit tests
- ✅ Using `uv` for environment reproducibility

### Performance (see "Asynchronous Programming", "Performance" sections)
- ✅ Asynchronicity for I/O-bound tasks with proper lifecycle management
- ✅ Profiling in production (`py-spy`) and development (`cProfile`)

### Documentation (see "Documentation" section)
- ✅ Documenting public interfaces and API examples
- ✅ README with architectural diagrams and usage examples

**Checking principle:** every commit should explain in 3 seconds **what** changed and **why**.

---
