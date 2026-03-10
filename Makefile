.PHONY: help run lint format check migrate-create migrate-up migrate-down seed create-admin test

# Default target
help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

run: ## Start the FastAPI development server
	uv run fastapi dev app/main.py

lint: ## Run ruff checks and formatting check
	uvx ruff check .
	uvx ruff format --check .

format: ## Run ruff check fix and formatting
	uvx ruff check --fix .
	uvx ruff format .

check: format lint ## Alias for format and lint

migrate-create: ## Create a new database migration (Usage: make migrate-create m="message")
	@if [ -z "$(m)" ]; then echo "Error: Migration message required. Usage: make migrate-create m=\"message\""; exit 1; fi
	uv run alembic revision --autogenerate -m "$(m)"

migrate-up: ## Run all pending database migrations
	uv run alembic upgrade head

migrate-down: ## Rollback the last database migration
	uv run alembic downgrade -1

seed: ## Seed the database with sample product data
	uv run python scripts/seed.py

create-admin: ## Create the default admin superuser
	uv run python scripts/create_admin.py

test: ## Run smoke tests using pytest
	PYTHONPATH=. uv run pytest tests/test_smoke.py
