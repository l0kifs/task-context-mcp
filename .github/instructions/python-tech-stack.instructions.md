---
applyTo: '**'
---
# Python Tech Stack

## Core Requirements
**MANDATORY**: Use only specified tools. Deviations require documented justification and approval.

**NOTE**: Different projects may use different subsets of this stack based on project specifics and requirements. Not all tools are mandatory for every project.

## Stack Components

### HTTP & Networking
- **httpx** - Async/sync HTTP client
  - Use for: All HTTP requests, API interactions
  - Docs: [https://www.python-httpx.org/]

- **fastapi** - Modern web framework for building APIs
  - Use for: REST API development, web services
  - Docs: [https://fastapi.tiangolo.com/]

### CLI Applications
- **typer** - CLI application framework
  - Use for: Command-line interface development
  - Docs: [https://typer.tiangolo.com/]

- **rich** - Rich text and beautiful formatting in the terminal
  - Use for: Rich text and beautiful formatting in the terminal
  - Docs: [https://rich.readthedocs.io/en/latest/]

### Logging
- **loguru** - Structured logging
  - Use for: Multi-level, informative logging, contextual logging with structured output
  - Docs: [https://loguru.readthedocs.io/en/stable/]

### Data Validation
- **pydantic** - Data validation & serialization
  - Use for: All data models, payload validation
  - Docs: [https://docs.pydantic.dev/latest/]

### Configuration
- **pydantic-settings** - Settings management
  - Use for: Centralized config, environment variables
  - Docs: [https://docs.pydantic.dev/latest/concepts/pydantic_settings/]

### Testing
- **pytest** - Testing framework
  - Use for: Unit, integration, functional tests
  - Docs: [https://docs.pytest.org/en/stable/getting-started.html]

- **pytest-cov** - Coverage reporting
  - Requirement: Minimum 90% coverage
  - Docs: [https://pytest-cov.readthedocs.io/en/latest/]

- **playwright** - End-to-end testing
  - Use for: Browser automation, E2E testing, web scraping
  - Docs: [https://playwright.dev/python/docs/intro]

### Code Quality
- **ruff** - Linting & formatting
  - Use for: Code standards enforcement
  - Docs: [https://docs.astral.sh/ruff/]

- **mypy** - Static type checking
  - Use for: Type safety validation
  - Docs: [https://mypy.readthedocs.io/en/stable/]

### Context Protocol
- **fastmcp** - Model Context Protocol
  - Use for: Context handling, MCP integration
  - Docs: [https://gofastmcp.com/getting-started/welcome]

### Project Management
- **uv** - Dependency & project management
  - Use for: Package management, virtual environments
  - Priority: Start all projects with uv setup
  - Docs: [https://docs.astral.sh/uv/]

### Database
- **sqlalchemy** - ORM & database toolkit
  - Use for: Database interactions, schema management
  - Docs: [https://docs.sqlalchemy.org/en/20/]

## Project Guidelines

### Essential Steps (when applicable)
- **Project initialization**: Use `uv` for dependency management when creating Python projects
- **Configuration**: Implement `pydantic-settings` for centralized config management
- **Logging**: Set up `loguru` for structured logging in applications

### Development Best Practices
- **HTTP operations**: Use `httpx` for all HTTP requests and API interactions
- **Web APIs**: Implement `fastapi` for REST API development and web services
- **CLI applications**: Use `typer` for command-line interface development
- **Data validation**: Apply `pydantic` for all data models and payload validation
- **Database layer**: Implement `sqlalchemy` for database operations when needed
- **Context handling**: Integrate `fastmcp` for MCP-based applications

### Quality Standards
- **Testing**: Write comprehensive tests with `pytest` for business logic
- **E2E Testing**: Use `playwright` for end-to-end testing of web applications
- **Coverage**: Maintain 90%+ test coverage using `pytest-cov` for critical applications
- **Code quality**: Ensure code passes `ruff` linting standards
- **Type safety**: Validate types with `mypy` static checking
- **API documentation**: Leverage `fastapi` automatic OpenAPI documentation for web APIs

## Compliance
Any deviation requires:
1. Documented technical justification
2. Approval from project lead
