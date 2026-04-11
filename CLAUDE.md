# AlcOpt

Fermentation tracking and optimization Streamlit app.

## Project Structure

```
alcopt/
├── app/                    # Streamlit multi-page app
│   ├── Home.py             # Landing page (leaderboard, analytics)
│   └── pages/
│       ├── 01_Tasting_Form.py
│       ├── 02_Brew_Log.py      # Admin only
│       ├── 03_Bottle_Log.py    # Admin only
│       └── 04_Information.py
├── auth.py                 # Google OAuth2 authentication
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   ├── queries.py          # Analytics queries (leaderboard)
│   └── utils.py            # DB session management, init
├── utils.py                # Fermentation math, unit conversions, plotting
└── streamlit_utils.py      # ORM-to-DataFrame display helpers
```

## Key Concepts

- **Fermentation** is the central entity. It has containers, ingredient additions, SG/mass measurements, and reviews.
- **Containers** are physical vessels (carboys, demijohns, bottles, etc.) unified in a single `containers` table with a `container_type` column. They are reusable across fermentations.
- **ContainerFermentationLog** records which container held which fermentation over what date range. This is the single source of truth for container contents — there are no denormalized FK caches.
- **IngredientAddition** records ingredients added to a container at a specific time. These are scoped to `container_id`, not `fermentation_id` — the fermentation is derived via the log. This allows adding ingredients before, during, or after fermentation (pre-soak, aging, post-bottling).
- **Reviews** rate any container (not just bottles) on 6 attributes (1-5 scale): overall, boldness, tannicity, sweetness, acidity, complexity.
- Admin-only pages are gated by `is_admin()` which checks the user's email against `ADMIN_EMAILS` env var.

## Database

- Default: SQLite at `data/alcopt.db`
- Connection string set via `DATABASE_URL` env var
- Schema defined via SQLAlchemy models in `alcopt/database/models.py`
- Schema is the source of truth; `init_db()` calls `Base.metadata.create_all`

## Running

```bash
# Docker (production)
docker compose up -d app

# Docker (dev, with live reload)
docker compose up -d app-dev

# Local
uv run streamlit run alcopt/app/Home.py
```

## Configuration

All config via environment variables (see `.env.example`):
- `DATABASE_URL` — database connection URI
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — OAuth2 credentials
- `GOOGLE_REDIRECT_URI` — OAuth redirect URL
- `ADMIN_EMAILS` — comma-separated admin emails
- Config loaded centrally in `alcopt/config.py`

## Deployment

- Dockerized with `python:3.11-slim-bookworm` base image
- Designed to run as a **git submodule** in a deploy monorepo (separate repos on GitHub, combined for deploy)
- **Railway** is the hosting platform:
  - Root directory set to this submodule's path in the deploy repo
  - Railway Postgres service provides `DATABASE_URL` env var (auto-linked)
  - `PORT` env var is set automatically by Railway and used in the Dockerfile CMD
  - All config via env vars (set in Railway dashboard)
- SQLite locally, PostgreSQL in production
- Base URL path set to `/alcopt` in `.streamlit/config.toml`

## Tooling

This project uses [uv](https://docs.astral.sh/uv/) for Python version management, dependency management, and running commands. Always use `uv run` to execute project code — it ensures the correct Python version and virtualenv are active.

```bash
uv run streamlit run alcopt/app/Home.py   # run the app
uv run python scripts/some_script.py      # run a script
uv run ruff check alcopt/                 # run linter
uv add <package>                          # add a dependency
uv remove <package>                       # remove a dependency
uv sync                                   # install from lockfile
```

## Linting & Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
uv run ruff check alcopt/ scripts/
uv run ruff check --fix alcopt/ scripts/
uv run ruff format alcopt/ scripts/
```

Run `ruff check` and `ruff format` before committing. Both should pass with zero issues.

## Dependencies

Managed with uv. Dependencies defined in `pyproject.toml`, locked in `uv.lock`. Python 3.11.

Core: streamlit, streamlit-oauth, sqlalchemy, pandas, numpy, matplotlib, seaborn, unum, opencv-python, psycopg2-binary
