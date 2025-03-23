import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

import streamlit as st
import os

from alcopt.database.models import Fermentation, Review, Bottle, SpecificGravityMeasurement
from alcopt.database.queries import get_fermentation_leaderboard
from alcopt.database.utils import init_db, get_db
from alcopt.auth import show_login_status
from alcopt.utils import get_ratings_abv_data, get_ratings_rs_data

st.set_page_config(
    page_title="Home",
    page_icon="🍷",
)

# Configure logging
log_filename = f"/data/logs/log_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),  # Log to a file with the current date
        logging.StreamHandler()  # Log to the console
    ]
)

init_db()
# Display login/logout button in the sidebar
show_login_status()

st.markdown(
    """
    Web App for recording tastings, brewing information, and tracking bottling.
"""
)

# Mead Average Ratings in a Leaderboard
st.markdown("## Mead Leaderboard")
st.title("Fermentation Leaderboard")


with get_db() as db:
    leaderboard_df = get_fermentation_leaderboard(db)
    st.dataframe(leaderboard_df, hide_index=True)

    # Plots
    reviews = db.query(Review).all()
    ratings = [review.overall_rating for review in reviews]
    st.markdown("## Overall Ratings")
    rating_hist = plt.figure()
    plt.hist(ratings, bins=[1, 2, 3, 4, 5], edgecolor="black") 
    plt.xlabel('Rating')
    plt.ylabel('# Reviews')
    st.pyplot(rating_hist)
    
    st.markdown("## Rating vs ABV")
    ratings, abvs = zip(*get_ratings_abv_data())
    m, b = np.polyfit(abvs, ratings, 1)
    fig = plt.figure() 
    plt.scatter(abvs, ratings) 
    x = np.array([min(abvs), max(abvs)])
    pred = m*x+b
    plt.plot(x, pred, alpha=.6, color='black', linestyle=":")
    plt.xlabel('ABV (%)')
    plt.ylabel('Overall Rating')
    st.pyplot(fig)
    
    st.markdown("## Rating vs Residual Sugar")
    ratings, rss = zip(*get_ratings_rs_data())
    m, b = np.polyfit(rss, ratings, 1)
    fig = plt.figure() 
    plt.scatter(rss, ratings) 
    x = np.array([min(rss), max(rss)])
    pred = m*x+b
    plt.plot(x, pred, alpha=.6, color='black', linestyle=":")
    plt.xlabel('Residual Sugar (g/L)')
    plt.ylabel('Overall Rating')
    st.pyplot(fig)