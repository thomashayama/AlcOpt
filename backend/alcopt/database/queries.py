import pandas as pd

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from alcopt.database.models import (
    ContainerFermentationLog,
    Fermentation,
    IngredientAddition,
    Review,
)


def get_fermentation_leaderboard(db: Session):
    """Average overall rating per fermentation, ordered descending."""
    query = (
        db.query(
            Fermentation.id,
            func.avg(Review.overall_rating).label("avg_rating"),
            func.count(Review.overall_rating).label("num_rating"),
        )
        .join(Review, Review.fermentation_id == Fermentation.id)
        .group_by(Fermentation.id)
        .order_by(func.avg(Review.overall_rating).desc())
    )

    results = query.all()

    leaderboard_df = pd.DataFrame(
        results, columns=["Fermentation ID", "Average Rating", "# Ratings"]
    )

    return leaderboard_df


def get_container_ingredient_additions(db: Session, container_id: int):
    """All ingredient additions for a container, ordered by added_at."""
    return (
        db.query(IngredientAddition)
        .filter(IngredientAddition.container_id == container_id)
        .order_by(IngredientAddition.added_at)
        .all()
    )


def get_fermentation_ingredient_additions(db: Session, fermentation_id: int):
    """All ingredient additions whose container held this fermentation at
    the time of addition.

    Uses inclusive bounds [start_date, end_date] on container_fermentation_logs.
    The data has been adjusted so that adjacent log windows don't share exact
    boundary timestamps, making inclusive comparison safe.
    """
    return (
        db.query(IngredientAddition)
        .options(joinedload(IngredientAddition.ingredient))
        .join(
            ContainerFermentationLog,
            ContainerFermentationLog.container_id == IngredientAddition.container_id,
        )
        .filter(
            ContainerFermentationLog.fermentation_id == fermentation_id,
            ContainerFermentationLog.start_date <= IngredientAddition.added_at,
            (ContainerFermentationLog.end_date.is_(None))
            | (ContainerFermentationLog.end_date >= IngredientAddition.added_at),
        )
        .order_by(IngredientAddition.added_at)
        .all()
    )
