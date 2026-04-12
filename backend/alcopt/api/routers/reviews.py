from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from alcopt.api.dependencies import (
    get_current_user,
    get_db,
    get_optional_user,
    require_admin,
)
from alcopt.api.schemas import ReviewCreate, ReviewOut
from alcopt.database.models import Container, Review
from alcopt.database.utils import current_fermentation_log, latest_fermentation_log

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut)
def create_review(
    body: ReviewCreate,
    db: Session = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    email = user["email"] if user else body.email
    if not email:
        raise HTTPException(400, "Email is required when not logged in")

    container = db.query(Container).get(body.container_id)
    if not container:
        raise HTTPException(404, f"Container {body.container_id} not found")

    review_dt = datetime.combine(body.tasting_date, datetime.now().time())
    log = current_fermentation_log(db, body.container_id, review_dt)
    if not log:
        log = latest_fermentation_log(db, body.container_id)
    if not log:
        raise HTTPException(400, "Container has never held a fermentation")

    review = Review(
        container_id=body.container_id,
        name=email,
        fermentation_id=log.fermentation_id,
        overall_rating=body.overall_rating,
        boldness=body.boldness,
        tannicity=body.tannicity,
        sweetness=body.sweetness,
        acidity=body.acidity,
        complexity=body.complexity,
        review_date=body.tasting_date,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/mine", response_model=list[ReviewOut])
def my_reviews(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return (
        db.query(Review)
        .filter(Review.name == user["email"])
        .order_by(Review.review_date.desc())
        .all()
    )


@router.get("", response_model=list[ReviewOut])
def all_reviews(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return db.query(Review).order_by(Review.review_date.desc()).all()
