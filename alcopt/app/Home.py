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
from alcopt.utils import get_ratings_abv_data, get_ratings_rs_data, reviews_to_df, plot_correlation_heatmap, plot_sweetness_vs_rating

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

st.markdown("""# AlcOpt""", help="Web App for recording tastings, brewing information, and tracking bottling.")
st.markdown('<a href="./Tasting_Form" target="_self">Go to Tasting Form</a>', unsafe_allow_html=True)

# Fermentation Average Ratings in a Leaderboard
st.markdown("## Fermentation Leaderboard")


with get_db() as db:
    leaderboard_df = get_fermentation_leaderboard(db)
    st.dataframe(leaderboard_df, hide_index=True)

    # Plots
    reviews = db.query(Review).all()
    reviews_df = reviews_to_df(reviews)

    st.pyplot(plot_correlation_heatmap(reviews_df))
    st.pyplot(plot_sweetness_vs_rating(reviews_df))
    
    ratings = [review.overall_rating for review in reviews]
    rating_hist = plt.figure(figsize=(8, 5))
    plt.hist(ratings, bins=np.arange(0.5, 6.5, 1), edgecolor="black", color="#4CAF50", alpha=0.8)
    plt.xticks(range(1, 6))
    plt.xlabel('Rating', fontsize=12)
    plt.ylabel('# Reviews', fontsize=12)
    plt.title('Distribution of Overall Ratings', fontsize=14, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(rating_hist)
    
    ratings, abvs = zip(*get_ratings_abv_data())
    m, b = np.polyfit(abvs, ratings, 1)
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(8, 5))
    # Scatter plot
    scatter = ax.scatter(abvs, ratings, color="#1f77b4", edgecolor="black", alpha=0.8, label="Data Points")
    # Regression line
    x = np.array([min(abvs), max(abvs)])
    pred = m * x + b
    ax.plot(x, pred, color="red", linestyle="--", linewidth=2, label="Trend Line")
    # Add labels, title, and grid
    ax.set_xlabel('ABV (%)', fontsize=12)
    ax.set_ylabel('Overall Rating', fontsize=12)
    ax.set_title('Overall Rating vs ABV', fontsize=14, fontweight='bold')
    ax.grid(axis='both', linestyle='--', alpha=0.7)
    # Add legend
    ax.legend(loc="best", fontsize=10)
    # Display the plot
    st.pyplot(fig)
    
    ratings, rss = zip(*get_ratings_rs_data())
    m, b = np.polyfit(rss, ratings, 1)
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(8, 5))
    # Scatter plot
    scatter = ax.scatter(rss, ratings, color="#ff7f0e", edgecolor="black", alpha=0.8, label="Data Points")
    # Regression line
    x = np.array([min(rss), max(rss)])
    pred = m * x + b
    ax.plot(x, pred, color="red", linestyle="--", linewidth=2, label="Trend Line")
    # Add labels, title, and grid
    ax.set_xlabel('Residual Sugar (g/L)', fontsize=12)
    ax.set_ylabel('Overall Rating', fontsize=12)
    ax.set_title('Overall Rating vs Residual Sugar', fontsize=14, fontweight='bold')
    ax.grid(axis='both', linestyle='--', alpha=0.7)
    # Add legend
    ax.legend(loc="best", fontsize=10)
    # Display the plot
    st.pyplot(fig)