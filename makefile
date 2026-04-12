# Variables
DOCKER_COMPOSE = docker compose

# Run backend locally
.PHONY: dev-backend
dev-backend:
	cd backend && uv run uvicorn alcopt.api.main:app --reload --port 8000

# Run frontend locally
.PHONY: dev-frontend
dev-frontend:
	cd frontend && npm run dev

# Deploy with Docker Compose
.PHONY: deploy
deploy:
	$(DOCKER_COMPOSE) up -d --build backend frontend

# Stop Docker Compose services
.PHONY: stop
stop:
	$(DOCKER_COMPOSE) down

# Clean
.PHONY: clean
clean:
	rm -rf backend/.venv backend/__pycache__ frontend/.next frontend/node_modules
