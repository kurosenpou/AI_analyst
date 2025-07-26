# AI Analyst Makefile
# Simplifies common development and deployment tasks

.PHONY: help build up down logs clean test lint format install dev prod backup restore health

# Default target
help:
	@echo "AI Analyst - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View service logs"
	@echo "  make clean       - Clean Docker resources"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Start production environment"
	@echo "  make backup      - Backup database"
	@echo "  make restore     - Restore database"
	@echo "  make health      - Check service health"
	@echo ""

# =============================================================================
# Development Commands
# =============================================================================

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed successfully!"

dev:
	@echo "Starting development environment..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "Press Ctrl+C to stop"
	@make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	@echo "Running backend tests..."
	cd backend && python -m pytest --cov=. --cov-report=html --cov-report=term
	@echo "Running frontend tests..."
	cd frontend && npm run test
	@echo "All tests completed!"

test-backend:
	cd backend && python -m pytest --cov=. --cov-report=html --cov-report=term

test-frontend:
	cd frontend && npm run test

lint:
	@echo "Running backend linting..."
	cd backend && flake8 . && mypy .
	@echo "Running frontend linting..."
	cd frontend && npm run lint
	@echo "Linting completed!"

lint-backend:
	cd backend && flake8 . && mypy .

lint-frontend:
	cd frontend && npm run lint

format:
	@echo "Formatting backend code..."
	cd backend && black .
	@echo "Formatting frontend code..."
	cd frontend && npm run format
	@echo "Code formatting completed!"

format-backend:
	cd backend && black .

format-frontend:
	cd frontend && npm run format

# =============================================================================
# Docker Commands
# =============================================================================

build:
	@echo "Building Docker images..."
	docker-compose build --no-cache
	@echo "Docker images built successfully!"

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started! Access points:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Grafana: http://localhost:3001 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"

down:
	@echo "Stopping all services..."
	docker-compose down
	@echo "All services stopped!"

restart:
	@echo "Restarting all services..."
	docker-compose restart
	@echo "All services restarted!"

logs:
	@echo "Viewing service logs (Press Ctrl+C to exit)..."
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f postgres

clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "Docker resources cleaned!"

clean-all:
	@echo "Cleaning all Docker resources (including images)..."
	docker-compose down -v --remove-orphans
	docker system prune -af
	@echo "All Docker resources cleaned!"

# =============================================================================
# Production Commands
# =============================================================================

prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production environment started!"

prod-build:
	@echo "Building production images..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
	@echo "Production images built!"

prod-down:
	@echo "Stopping production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "Production environment stopped!"

# =============================================================================
# Database Commands
# =============================================================================

backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U ai_analyst_user ai_analyst > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created in backups/ directory!"

restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker-compose exec -T postgres psql -U ai_analyst_user ai_analyst < backups/$$backup_file
	@echo "Database restored successfully!"

db-shell:
	@echo "Opening database shell..."
	docker-compose exec postgres psql -U ai_analyst_user ai_analyst

db-reset:
	@echo "Resetting database..."
	docker-compose down postgres
	docker volume rm ai_analyst_postgres_data
	docker-compose up -d postgres
	@echo "Database reset completed!"

# =============================================================================
# Monitoring Commands
# =============================================================================

health:
	@echo "Checking service health..."
	@echo "Backend API:"
	@curl -f http://localhost:8000/health || echo "Backend API is down"
	@echo "\nFrontend:"
	@curl -f http://localhost:3000 || echo "Frontend is down"
	@echo "\nDatabase:"
	@docker-compose exec postgres pg_isready -U ai_analyst_user || echo "Database is down"
	@echo "\nRedis:"
	@docker-compose exec redis redis-cli ping || echo "Redis is down"
	@echo "\nHealth check completed!"

status:
	@echo "Service status:"
	docker-compose ps

stats:
	@echo "Resource usage:"
	docker stats --no-stream

# =============================================================================
# Utility Commands
# =============================================================================

shell-backend:
	@echo "Opening backend shell..."
	docker-compose exec backend /bin/bash

shell-frontend:
	@echo "Opening frontend shell..."
	docker-compose exec frontend /bin/sh

update:
	@echo "Updating dependencies..."
	cd backend && pip install --upgrade -r requirements.txt
	cd frontend && npm update
	@echo "Dependencies updated!"

security-scan:
	@echo "Running security scan..."
	cd backend && safety check
	cd frontend && npm audit
	@echo "Security scan completed!"

# =============================================================================
# CI/CD Commands
# =============================================================================

ci:
	@echo "Running CI pipeline..."
	make lint
	make test
	make build
	@echo "CI pipeline completed successfully!"

deploy:
	@echo "Deploying to production..."
	make prod-build
	make backup
	make prod
	make health
	@echo "Deployment completed!"

# =============================================================================
# Documentation Commands
# =============================================================================

docs:
	@echo "Generating documentation..."
	cd backend && python -m pydoc -w .
	cd frontend && npm run docs
	@echo "Documentation generated!"

docs-serve:
	@echo "Serving documentation..."
	@echo "API docs available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"

# =============================================================================
# Environment Setup
# =============================================================================

setup:
	@echo "Setting up AI Analyst development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	make install
	@echo "\nSetup completed! Next steps:"
	@echo "1. Edit .env file with your configuration"
	@echo "2. Run 'make dev' to start development environment"
	@echo "3. Run 'make up' to start with Docker"

setup-prod:
	@echo "Setting up production environment..."
	@if [ ! -f .env ]; then echo "Error: .env file not found. Please create it first."; exit 1; fi
	make prod-build
	make prod
	@echo "Production environment setup completed!"

# =============================================================================
# Maintenance Commands
# =============================================================================

maintenance:
	@echo "Running maintenance tasks..."
	make backup
	make clean
	make security-scan
	@echo "Maintenance completed!"

monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3001; \
		open http://localhost:9090; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3001; \
		xdg-open http://localhost:9090; \
	else \
		echo "Please open the URLs manually in your browser"; \
	fi