# AI Dungeon Master - Development Commands
.PHONY: help dev-up dev-down test-backend test-frontend test-e2e test-all lint format migrate install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Environment ---

install: ## Install all dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev-up: ## Start development databases (PostgreSQL, MongoDB, Redis)
	docker compose -f docker-compose.dev.yml up -d
	@echo "Waiting for services to be healthy..."
	@docker compose -f docker-compose.dev.yml exec postgres pg_isready -U dungeonmaster --quiet 2>/dev/null || sleep 5

dev-down: ## Stop development databases
	docker compose -f docker-compose.dev.yml down

dev-clean: ## Stop and remove all dev data
	docker compose -f docker-compose.dev.yml down -v

# --- Backend ---

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --tb=short

test-backend-cov: ## Run backend tests with coverage
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linters
	cd backend && python -m ruff check app/ tests/
	cd backend && python -m ruff format --check app/ tests/

format: ## Auto-format code
	cd backend && python -m ruff format app/ tests/
	cd backend && python -m ruff check --fix app/ tests/

# --- Frontend ---

test-frontend: ## Run frontend unit tests
	cd frontend && npm test -- --run

test-frontend-watch: ## Run frontend tests in watch mode
	cd frontend && npm test

# --- E2E ---

test-e2e: ## Run Playwright end-to-end tests
	cd frontend && npx playwright test

# --- Integration ---

test-all: ## Run all tests (backend + frontend + E2E)
	$(MAKE) test-backend
	$(MAKE) test-frontend
	@echo ""
	@echo "====================================="
	@echo "  All tests passed!"
	@echo "====================================="

# --- Database ---

migrate: ## Run Alembic migrations
	cd backend && python -m alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="description")
	cd backend && python -m alembic revision --autogenerate -m "$(MSG)"
