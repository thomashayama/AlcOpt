from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from alcopt.api.dependencies import get_db
from alcopt.api.schemas import LeaderboardEntry
from alcopt.database.models import Review
from alcopt.database.queries import get_fermentation_leaderboard
from alcopt.utils import get_ratings_abv_data, get_ratings_rs_data, reviews_to_df

router = APIRouter(prefix="/api", tags=["home"])


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    df = get_fermentation_leaderboard(db)
    page = df.iloc[offset : offset + limit]
    return [
        LeaderboardEntry(
            rank=offset + i + 1,
            fermentation_id=int(row["Fermentation ID"]),
            avg_rating=round(row["Average Rating"], 2),
            num_ratings=int(row["# Ratings"]),
        )
        for i, row in page.iterrows()
    ]


@router.get("/analytics/reviews")
def analytics_reviews(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    reviews = db.query(Review).offset(offset).limit(limit).all()
    return reviews_to_df(reviews)


@router.get("/analytics/ratings-abv")
def analytics_ratings_abv(db: Session = Depends(get_db)):
    return get_ratings_abv_data(db)


@router.get("/analytics/ratings-rs")
def analytics_ratings_rs(db: Session = Depends(get_db)):
    return get_ratings_rs_data(db)
