import streamlit as st
import pandas as pd
import numpy as np

# SQL
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from alcopt.database.models import Fermentation, Bottle, Review
from alcopt.database.utils import get_db
from datetime import datetime

st.set_page_config(
    page_title="Tasting Form",
    page_icon="🍷",
)

if "df" not in st.session_state:
    try:
        st.session_state.df = pd.read_csv("../data/tasting.csv")
    except:
        st.session_state.df = pd.DataFrame()
if "last_data" not in st.session_state:
    st.session_state.last_data = {}


with st.form("Tasting Form"):
    name = st.text_input("Full Name", placeholder=st.session_state.last_data.get("name", "John Doe"), autocomplete="on")
    bottle_id = st.number_input("Bottle ID", value=1, min_value=1, step=1)
    date = st.date_input("Tasting Date")
    overall_rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    boldness = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    tannicity = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    sweetness = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    acidity = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)

    if st.form_submit_button('Submit'):
        # Open a session
        with get_db() as db:
            review_date = datetime.now()  # Replace with the actual review_date

            bottle = db.query(Bottle).filter_by(id=bottle_id).first()

            if not bottle:
                st.error(f"No bottle found with id {bottle_id}")
            elif bottle.fermentation_id is None:
                st.error(f"Bottle is empty!")
            else:
                # Create a new review
                new_review = Review(
                    bottle_id=bottle_id,
                    fermentation_id=bottle.fermentation_id,
                    overall_rating=overall_rating,
                    boldness=boldness,
                    tannicity=tannicity,
                    sweetness=sweetness,
                    acidity=acidity,
                    complexity=complexity,
                    review_date=date
                )

                # Add and commit the review to the session
                db.add(new_review)
                db.commit()

                st.success("Review added successfully!")
                st.session_state.last_data["name"] = name

                st.rerun()

# conn.reset()
# tasting_table = conn.query("SELECT * FROM tasting ORDER BY taste_date DESC;")
with get_db() as db:
    reviews = db.query(Review).order_by(desc(Review.review_date)).all()

    # Convert to a list of dictionaries
    reviews_list = [
        {
            'Bottle ID': review.bottle_id,
            'Overall Rating': review.overall_rating,
            'Boldness': review.boldness,
            'Tannicity': review.tannicity,
            'Sweetness': review.sweetness,
            'Acidity': review.acidity,
            'Complexity': review.complexity,
            'Review Date': review.review_date
        }
        for review in reviews
    ]

    # Convert list of dictionaries to a DataFrame
    reviews_df = pd.DataFrame(reviews_list)

    # Display the DataFrame
    st.dataframe(reviews_df, use_container_width=True, hide_index=True)
