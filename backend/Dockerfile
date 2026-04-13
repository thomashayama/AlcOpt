FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

FROM python:3.11-slim-bookworm

WORKDIR /app
COPY --from=builder /app /app

CMD ["sh", "-c", "/app/.venv/bin/uvicorn alcopt.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
