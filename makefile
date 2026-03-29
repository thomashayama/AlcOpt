# Variables
PYTHON = python
VENV_DIR = .venv
SECRETS_FILE = secrets.toml
APP_FILE = alcopt/app/Home.py
DOCKER_COMPOSE = docker compose
PORT = 8501

# Detect OS for virtual environment activation
ifeq ($(OS),Windows_NT)
    ACTIVATE = .venv\Scripts\activate
else
    ACTIVATE = . .venv/bin/activate
endif

# Create a virtual environment
.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Activating virtual environment and installing dependencies..."
	$(ACTIVATE) && pip install --upgrade pip && pip install -r requirements.txt

# Install dependencies
.PHONY: install
install:
	@echo "Installing dependencies..."
	$(ACTIVATE) && pip install -r requirements.txt 

# Load secrets from secrets.toml and run Streamlit
.PHONY: local
local:
	@echo "Loading secrets from $(SECRETS_FILE)..."
	@$(foreach line,$(shell cat $(SECRETS_FILE) | grep -v '^#' | sed 's/ = /=/g'), $(EXPORT_CMD) $(line);)
	@echo "Starting Streamlit locally with OAuth..."
	$(ACTIVATE) && streamlit run $(APP_FILE) --server.port $(PORT) --server.fileWatcherType none

# Deploy with Docker Compose
.PHONY: deploy
deploy:
	@echo "Deploying the app using Docker Compose..."
	$(DOCKER_COMPOSE) up -d --build

# Stop Docker Compose services
.PHONY: stop
stop:
	@echo "Stopping Docker Compose services..."
	$(DOCKER_COMPOSE) down

# Clean virtual environment
.PHONY: clean
clean:
	@echo "Cleaning up environment..."
	rm -rf $(VENV_DIR) __pycache__ .streamlit