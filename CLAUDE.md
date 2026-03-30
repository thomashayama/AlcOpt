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
- Admin-only pages are gated by `is_admin()` which checks the user's email against `secrets.security.admin`.

## Database

- Default: SQLite at `/data/alcopt.db`
- Connection string configured in `.streamlit/secrets.toml` under `[connections.alcopt_db]`
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

Secrets go in `.streamlit/secrets.toml` (see `secrets-example.toml`):
- `[connections.alcopt_db]` - Database URI
- `[oauth.google]` - OAuth2 credentials
- `[security]` - Admin email list

## Deployment

- Dockerized with `python:3.11-slim-buster` base image
- Designed to run as a **git submodule** in a deploy monorepo (separate repos on GitHub, combined for deploy)
- **Railway** is the hosting platform:
  - Root directory set to this submodule's path in the deploy repo
  - Railway Postgres service provides `DATABASE_URL` env var (auto-linked)
  - `PORT` env var is set automatically by Railway and used in the Dockerfile CMD
  - `SECRETS_FILE` env var points to the secrets TOML
- The app reads `DATABASE_URL` first, falls back to `secrets["connections"]["alcopt_db"]["uri"]` (see `database/utils.py:16`)
- SQLite locally, PostgreSQL in production
- Base URL path set to `/alcopt` in `.streamlit/config.toml`

## Dependencies

Core: streamlit, streamlit-oauth, sqlalchemy, pandas, numpy, matplotlib, seaborn, unum, opencv-python, psycopg2-binary
