import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

from sqlalchemy.orm import Session
from sqlalchemy import func

import streamlit as st
from streamlit_oauth import OAuth2Component
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"

oauth2 = OAuth2Component(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "https://accounts.google.com/o/oauth2/auth", "https://oauth2.googleapis.com/token")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    result = oauth2.authorize_button("Login with Google", REDIRECT_URI)
    if result:
        st.session_state.user = result.get("userinfo", {}).get("email")
        st.experimental_rerun()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user}**")
    if st.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()


from alcopt.database.models import Fermentation, Review, Bottle, SpecificGravityMeasurement
from alcopt.database.queries import get_fermentation_leaderboard
from alcopt.database.utils import init_db, get_db

st.set_page_config(
    page_title="Home",
    page_icon="🍷",
)

init_db()

st.markdown(
    """
    Web App for recording tastings, brewing information, and tracking bottling.
"""
)

# st.page_link("pages/01_Tasting_Form.py", label="Tasting Form", icon="1️⃣")
# st.page_link("pages/02_Brew_Log.py", label="Brew Logging", icon="2️⃣")
# st.page_link("pages/03_Bottle_Log.py", label="Bottle Logging", icon="2️⃣")

# Mead Average Ratings in a Leaderboard
st.markdown("## Mead Leaderboard")
st.title("Fermentation Leaderboard")

def sg_to_sugar(sg):
    """
    Convert specific gravity to sugar content in grams per liter.

    Parameters:
    sg (float): Specific gravity.

    Returns:
    float: Sugar content in grams per liter.
    """
    return (sg - 1) * 10_000

def get_ratings_abv_data():
    with get_db() as db:
        data = db.query(
            Review.overall_rating,
            SpecificGravityMeasurement.fermentation_id,
            func.max(SpecificGravityMeasurement.specific_gravity).label('initial_sg'),
            func.min(SpecificGravityMeasurement.specific_gravity).label('final_sg')
        ).join(
            Bottle, Review.bottle_id == Bottle.id
        ).join(
            Fermentation, Bottle.fermentation_id == Fermentation.id
        ).join(
            SpecificGravityMeasurement, Fermentation.id == SpecificGravityMeasurement.fermentation_id
        ).group_by(
            Review.id
        ).all()

        ratings_abv = []
        for row in data:
            initial_sg = row.initial_sg
            final_sg = row.final_sg
            abv = (initial_sg - final_sg) * 131.25
            ratings_abv.append((row.overall_rating, abv))

        return ratings_abv

def get_ratings_rs_data():
    with get_db() as db:
        data = db.query(
            Review.overall_rating,
            SpecificGravityMeasurement.fermentation_id,
            func.min(SpecificGravityMeasurement.specific_gravity).label('final_sg')
        ).join(
            Bottle, Review.bottle_id == Bottle.id
        ).join(
            Fermentation, Bottle.fermentation_id == Fermentation.id
        ).join(
            SpecificGravityMeasurement, Fermentation.id == SpecificGravityMeasurement.fermentation_id
        ).group_by(
            Review.id
        ).all()

        ratings_rs = []
        for row in data:
            rs = sg_to_sugar(row.final_sg)
            ratings_rs.append((row.overall_rating, rs))

        return ratings_rs

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