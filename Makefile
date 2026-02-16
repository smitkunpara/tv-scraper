.PHONY: help lint format format-check type-check test test-cov check ci install-hooks clean

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Install pre-commit hooks
install-hooks:  ## Install pre-commit hooks
	uv run pre-commit install

# Code quality checks
lint:  ## Run ruff linter on source code
	uv run ruff check tv_scraper/

format:  ## Auto-format code with ruff
	uv run ruff format tv_scraper/

format-check:  ## Check if code is formatted correctly
	uv run ruff format --check tv_scraper/

type-check:  ## Run mypy type checker
	uv run mypy tv_scraper/

# Testing
test:  ## Run unit and integration tests
	uv run pytest tests/unit tests/integration -v

test-cov:  ## Run tests with coverage report
	uv run pytest tests/unit tests/integration -v --cov=tv_scraper --cov-report=term-missing

test-all:  ## Run all tests including live API tests
	uv run pytest tests/ -v

# Combined checks (mimics CI)
check:  ## Run all quality checks (lint, format, type-check, test)
	@echo "Running linter..."
	@make lint
	@echo "\nChecking formatting..."
	@make format-check
	@echo "\nRunning type checker..."
	@make type-check || echo "Type check warnings found (non-blocking)"
	@echo "\nRunning tests..."
	@make test

ci:  ## Full CI simulation (lint, format, type-check, test with coverage)
	@echo "=== Running CI Checks ==="
	@echo "\n1. Linting..."
	@make lint
	@echo "\n2. Format check..."
	@make format-check
	@echo "\n3. Type checking..."
	@make type-check || echo "Type check warnings found (non-blocking)"
	@echo "\n4. Tests with coverage..."
	@make test-cov
	@echo "\n=== CI Checks Complete ==="

# Cleanup
clean:  ## Clean up cache files and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/
