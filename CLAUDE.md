# AlcOpt

Fermentation tracking and optimization Streamlit app. Multi-page Streamlit frontend, SQLAlchemy ORM, Google OAuth, SQLite locally and PostgreSQL in production (Railway).

## Environment

- **OS**: Windows 11. You're running under a bash shell (Git Bash / MSYS), so use Unix syntax (`/dev/null`, forward slashes), not Windows cmd syntax. Long-running commands may behave differently than on Linux — prefer `uv run` wrappers over bare binaries.
- **Python**: 3.11, managed by [uv](https://docs.astral.sh/uv/). Always invoke project code via `uv run ...` so the correct interpreter and venv are used.
- **Database**: SQLite at `data/alcopt.db` locally; `DATABASE_URL` env var overrides. Schema is the source of truth — it's defined in `alcopt/database/models.py` and materialized by `init_db()` via `Base.metadata.create_all`. There are no migrations.

## Domain model (non-obvious)

These relationships matter for any query or feature work and aren't obvious from the schema alone:

- **Containers** are physical vessels (carboys, demijohns, bottles, …) unified in one `containers` table with a `container_type` discriminator. They are reused across fermentations.
- **ContainerFermentationLog** is the single source of truth for which container held which fermentation over what date range. There are no denormalized FK caches on `containers` or `fermentations` — always join through the log.
- **IngredientAddition** rows are scoped to `container_id`, not `fermentation_id`. The fermentation is derived via the log. This is intentional — it supports pre-soak, aging, and post-bottling additions that fall outside the fermentation window.
- Date-range joins against the log use **inclusive** `start_date` / `end_date` bounds. Recent bugs (see `da8ef87`, `7adff36`) came from treating `end_date` as exclusive.
- **Reviews** rate any container (not only bottles) on 6 attributes (1–5): overall, boldness, tannicity, sweetness, acidity, complexity.
- Admin-only pages are gated by `is_admin()`, which checks the user's email against the `ADMIN_EMAILS` env var.

## Common commands

```bash
uv run streamlit run alcopt/app/Home.py   # run app locally
uv run ruff check alcopt/ scripts/        # lint
uv run ruff format alcopt/ scripts/       # format
docker compose up -d app-dev              # dev container (live reload)
```

Run `ruff check` and `ruff format` before committing — both must pass with zero issues.

## Deployment notes

- This repo is consumed as a **git submodule** inside a separate deploy monorepo. Don't add deploy-repo-specific config here.
- Hosted on **Railway** at `alcopt.thomashayama.com` (subdomain — the apex `thomashayama.com` belongs to a separate Railway project for the personal site). `DATABASE_URL` and `PORT` are injected by Railway; Postgres is the prod DB. App is served at the root of its subdomain — no `baseUrlPath` override.
- All config flows through env vars — see `.env.example` and `alcopt/config.py`.
