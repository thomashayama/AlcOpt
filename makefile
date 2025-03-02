# Variables
PYTHON = python
VENV_DIR = .venv
SECRETS_FILE = secrets.toml
APP_FILE = alcopt/app/Home.py
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

# Run the Streamlit app with OAuth and secrets locally
.PHONY: local
local:
	@echo "Starting Streamlit locally with OAuth..."
	$(ACTIVATE) && streamlit run $(APP_FILE) --server.port $(PORT) --server.fileWatcherType none

# Deploy to Streamlit Cloud (if applicable)
.PHONY: deploy
deploy:
	@echo "Deploying to Streamlit Cloud..."
	@git add .
	@git commit -m "Deploying Streamlit app"
	@git push origin main

# Clean virtual environment
.PHONY: clean
clean:
	@echo "Cleaning up environment..."
	rm -rf $(VENV_DIR) __pycache__ .streamlit