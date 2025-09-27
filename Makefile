.PHONY: install test test-unit test-integration lint format type-check security config-check architecture-check all

install:
	uv sync

test: test-unit test-integration

test-unit:
	uv run pytest tests/unit/ --cov=src/task_context_mcp --cov-report=html --cov-report=term

test-integration:
	uv run pytest tests/integration/ --cov=src/task_context_mcp --cov-report=html --cov-report=term

test-e2e:
	uv run pytest tests/e2e/ --cov=src/task_context_mcp --cov-report=html --cov-report=term

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

type-check:
	uv run mypy src

security:
	uv run bandit -r src/

config-check:
	# Validate configurations for all environments
	uv run python -c "import os; from src.task_context_mcp.config.settings import get_settings; os.environ['ENVIRONMENT'] = 'development'; get_settings(); os.environ['ENVIRONMENT'] = 'testing'; get_settings(); os.environ['ENVIRONMENT'] = 'production'; get_settings(); print('✓ All environment configs valid')"

architecture-check:
	# Check architectural principles compliance
	python scripts/check_dependencies.py

clean:
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

all: format lint type-check config-check test security