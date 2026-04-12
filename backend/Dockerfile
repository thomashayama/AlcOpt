FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN uv sync --frozen

CMD ["sh", "-c", "uv run uvicorn alcopt.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
