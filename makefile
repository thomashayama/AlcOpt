# Variables
DOCKER_COMPOSE = docker compose

# Run backend locally (no Docker)
.PHONY: dev-backend
dev-backend:
	cd backend && uv run uvicorn alcopt.api.main:app --reload --port 8000

# Run frontend locally (no Docker)
.PHONY: dev-frontend
dev-frontend:
	cd frontend && npm run dev

# Docker: build and start both services
.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d --build backend frontend

# Docker: start dev backend with live reload
.PHONY: up-dev
up-dev:
	$(DOCKER_COMPOSE) up -d --build backend-dev

# Docker: stop all services
.PHONY: down
down:
	$(DOCKER_COMPOSE) down

# Docker: view logs
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Run backend tests
.PHONY: test
test:
	cd backend && uv run python -m pytest tests/ -v

# Clean
.PHONY: clean
clean:
	rm -rf backend/.venv backend/__pycache__ frontend/.next frontend/node_modules
