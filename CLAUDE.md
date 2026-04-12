# AlcOpt

Fermentation tracking and optimization app. FastAPI backend + Next.js frontend, SQLAlchemy ORM, Google OAuth with JWT auth, SQLite locally and PostgreSQL in production (Railway).

## Architecture

- **Backend** (`backend/`): FastAPI, SQLAlchemy, Python 3.11, managed by uv
- **Frontend** (`frontend/`): Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Auth**: Google OAuth redirect flow → JWT in httpOnly cookies
- **Theme**: Wine-cellar dark (burgundy #A4243B, gold #D4A24C, dark brown backgrounds)

## Environment

- **OS**: Windows 11. You're running under a bash shell (Git Bash / MSYS), so use Unix syntax (`/dev/null`, forward slashes), not Windows cmd syntax.
- **Python**: 3.11, managed by [uv](https://docs.astral.sh/uv/). Always invoke backend code via `cd backend && uv run ...`.
- **Node**: 20+. Frontend uses npm.
- **Database**: SQLite at `data/alcopt.db` locally; `DATABASE_URL` env var overrides. Schema is defined in `backend/alcopt/database/models.py` and materialized by `init_db()`. There are no migrations.

## Domain model (non-obvious)

- **Containers** are physical vessels (carboys, demijohns, bottles, …) unified in one `containers` table with a `container_type` discriminator. They are reused across fermentations.
- **ContainerFermentationLog** is the single source of truth for which container held which fermentation over what date range. There are no denormalized FK caches — always join through the log.
- **IngredientAddition** rows are scoped to `container_id`, not `fermentation_id`. The fermentation is derived via the log.
- Date-range joins against the log use **inclusive** `start_date` / `end_date` bounds.
- **Reviews** rate any container on 6 attributes (1–5): overall, boldness, tannicity, sweetness, acidity, complexity.
- Admin-only routes are gated by `require_admin` dependency, which checks the JWT email against `ADMIN_EMAILS`.

## Common commands

```bash
# Backend
cd backend && uv run uvicorn alcopt.api.main:app --reload --port 8000
cd backend && uv run ruff check alcopt/
cd backend && uv run ruff format alcopt/

# Frontend
cd frontend && npm run dev
cd frontend && npm run build

# Docker
docker compose up -d backend frontend
```

Run `ruff check` and `ruff format` on backend before committing — both must pass with zero issues.

## Deployment notes

- This repo is consumed as a **git submodule** inside a separate deploy monorepo.
- Hosted on **Railway** at `alcopt.thomashayama.com`. Two services: backend (FastAPI) and frontend (Next.js).
- `DATABASE_URL`, `PORT`, `JWT_SECRET`, `FRONTEND_URL` are injected by Railway.
- All config flows through env vars — see `.env.example` and `backend/alcopt/config.py`.
