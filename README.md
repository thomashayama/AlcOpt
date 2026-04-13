```
            _         ____          _
     /\    | |       / __ \        | |
    /  \   | |  ___ | |  | | _ __  | |_
   / /\ \  | | / __|| |  | || '_ \ | __|
  / ____ \ | || (__ | |__| || |_) || |_
 /_/    \_\|_| \___| \____/ | .__/  \__|
                            | |
                            |_|
```

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License](https://img.shields.io/github/license/thomashayama/AlcOpt?branch=Main)](https://github.com/thomashayama/AlcOpt/blob/Main/LICENSE)

Deployed to https://alcopt.thomashayama.com/

A fermentation tracking and optimization web app. Log brews, track ingredients, record specific gravity and mass measurements, manage vessels and bottles, and review finished products with detailed tasting profiles.

## Features

- **Brew Logging** - Track fermentations with ingredients, vessels, SG/mass measurements, racking, and bottling
- **Tasting Reviews** - Rate bottles on overall quality, boldness, tannicity, sweetness, acidity, and complexity
- **Leaderboard & Analytics** - Rank fermentations by average rating, view correlation heatmaps and rating distributions
- **ABV & Sugar Calculations** - Predict potential ABV and residual sugar from ingredients and gravity readings
- **Vessel & Bottle Management** - Track carboys, demijohns, and individual bottles through the fermentation lifecycle
- **Label Generation** - Print QR-code label sheets with Truchet-tile designs for containers
- **Google OAuth** - Authentication with role-based admin access

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Python 3.11, managed by [uv](https://docs.astral.sh/uv/)
- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Database**: SQLite locally, PostgreSQL in production
- **Auth**: Google OAuth2 redirect flow with JWT in httpOnly cookies
- **Infrastructure**: Docker, Railway

## Run

```bash
# Docker
docker compose up -d backend frontend

# Or run services individually:

# Backend
cd backend && uv run uvicorn alcopt.api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

## Development

```bash
# Install backend dependencies
cd backend && uv sync

# Install frontend dependencies
cd frontend && npm install

# Lint & format
cd backend && uv run ruff check alcopt/ && uv run ruff format alcopt/
cd frontend && npm run lint

# Run tests
cd backend && uv run pytest
```

## Configuration

Copy `.env.example` to `.env` and fill in:
- `DATABASE_URL` - database connection URI (defaults to SQLite)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth2 credentials
- `GOOGLE_REDIRECT_URI` - OAuth redirect URL
- `JWT_SECRET` - secret key for JWT signing
- `FRONTEND_URL` - frontend origin for CORS and redirects
- `ADMIN_EMAILS` - comma-separated list of admin emails

## Deployment (Railway)

This repo is designed to be used as a **git submodule** in a deploy monorepo. On Railway:

1. Add this repo as a submodule in your deploy repo
2. Create backend and frontend services, each pointing to their subdirectory
3. Add a **Postgres** service - Railway provides `DATABASE_URL` automatically
4. Set environment variables:
   - `DATABASE_URL` - provided by Railway Postgres (auto-linked)
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth credentials
   - `GOOGLE_REDIRECT_URI` - OAuth redirect URL
   - `JWT_SECRET` - secret for JWT signing
   - `FRONTEND_URL` - e.g. `https://alcopt.thomashayama.com`
   - `ADMIN_EMAILS` - comma-separated admin emails
   - `PORT` - set automatically by Railway
