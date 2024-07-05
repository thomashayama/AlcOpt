import pandas as pd

import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

from sqlalchemy.orm import Session
from sqlalchemy import func

from alcopt.database.models import Fermentation, Review


def get_fermentation_leaderboard(db: Session):
    # Query to get average overall rating for each fermentation
    query = (
        db.query(
            Fermentation.id,
            func.avg(Review.overall_rating).label('avg_rating'),
            func.count(Review.overall_rating).label('num_rating'),
        )
        .join(Review, Review.fermentation_id == Fermentation.id)
        .group_by(Fermentation.id)
        .order_by(func.avg(Review.overall_rating).desc())
    )
    
    results = query.all()
    
    # Create DataFrame from query results
    leaderboard_df = pd.DataFrame(results, columns=['Fermentation ID', 'Average Rating', '# Ratings'])
    
    return leaderboard_df