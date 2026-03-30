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

- **Fermentation** is the central entity. It has vessels, ingredients, SG/mass measurements, bottles, and reviews.
- **Vessels** are reusable containers (carboys, demijohns). **Bottles** are individual end products.
- **Reviews** rate bottles on 6 attributes (1-5 scale): overall, boldness, tannicity, sweetness, acidity, complexity.
- Admin-only pages are gated by `is_admin()` which checks the user's email against `ADMIN_EMAILS` env var.

## Database

- Default: SQLite at `data/alcopt.db`
- Connection string set via `DATABASE_URL` env var
- Schema defined via SQLAlchemy models in `alcopt/database/models.py`
- Reference SQL schema in `schema.sql`

## Running

```bash
# Docker (production)
docker compose up -d app

# Docker (dev, with live reload)
docker compose up -d app-dev

# Local
make local
# or: streamlit run alcopt/app/Home.py
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

## Dependencies

Core: streamlit, streamlit-oauth, sqlalchemy, pandas, numpy, matplotlib, seaborn, unum, opencv-python, psycopg2-binary
