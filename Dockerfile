FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 git -y

COPY . /app
WORKDIR /app

RUN uv sync --frozen

CMD ["sh", "-c", "uv run streamlit run /app/alcopt/app/Home.py --server.port=$PORT --server.address=0.0.0.0"]
