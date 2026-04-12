from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alcopt.config import FRONTEND_URL
from alcopt.database.utils import init_db
from alcopt.api.routers import auth, home, reviews, brew, containers, labels


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AlcOpt", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(home.router)
app.include_router(reviews.router)
app.include_router(brew.router)
app.include_router(containers.router)
app.include_router(labels.router)
