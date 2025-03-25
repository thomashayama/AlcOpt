import streamlit as st
from time import time
from datetime import datetime
import logging

# SQL
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from alcopt.database.models import Fermentation, Bottle, Review
from alcopt.database.utils import get_db
from alcopt.auth import get_user_token, show_login_status, is_admin
from alcopt.utils import reviews_to_df, plot_correlation_heatmap, plot_sweetness_vs_rating, plot_user_rating_distribution

st.set_page_config(
    page_title="Tasting Form",
    page_icon="🍷",
)

# Show login/logout button
token = show_login_status()

# if not token:
#     st.warning("🔒 Please log in to access this page.")
#     st.stop()
email = None
if "user_email" in st.session_state:
    email = st.session_state.user_email
else:
    col1, col2 = st.columns([2, 2])
    with col1:
        token = get_user_token(button_key="page_login")
    if token:
        st.rerun()
    with col2:
        st.info("Recommended to logging in")
with st.form("Tasting Form"):
    # Inject CSS for larger slider
    st.markdown(
        """
        <style>
            /* Make slider thumb larger */
            .stSlider > div[data-baseweb="slider"] > div {
                padding: 20px 0px;
            }

            /* Make the track thicker */
            .stSlider .rc-slider-track {
                height: 10px !important;
            }

            /* Increase the size of the draggable circle */
            .stSlider .rc-slider-handle {
                width: 30px !important;
                height: 130px !important;
                margin-top: -12px !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    if email is not None:
        name = email
    else:
        name = st.text_input("Full Name", placeholder="John Doe", autocomplete="on")
    bottle_id = st.number_input("Bottle ID", value=0, min_value=0, step=1)
    date = st.date_input("Tasting Date")
    overall_rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    boldness = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    tannicity = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    sweetness = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    acidity = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)

    if st.form_submit_button('Submit'):
        if bottle_id == 0:
            st.error("Please input a valid Bottle ID")
        else:
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
                        name=name,
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
                    logging.info(f"Tasting Form Submitted by {name} for Bottle ID {bottle_id}")
                    


with get_db() as db:
    if email is not None:
        st.markdown("## Your Review History")
        user_reviews = db.query(Review).filter(Review.name == email).order_by(desc(Review.review_date)).all()

        user_reviews_df = reviews_to_df(user_reviews)

        # Display the DataFrame
        st.dataframe(user_reviews_df, use_container_width=True, hide_index=True)

        st.pyplot(plot_correlation_heatmap(user_reviews_df))

        # Get all reviews
        if is_admin():
            st.markdown("## All Review History")
            reviews = db.query(Review).order_by(desc(Review.review_date)).all()

            reviews_df = reviews_to_df(reviews)

            # Display the DataFrame
            st.dataframe(reviews_df, use_container_width=True, hide_index=True)
            st.pyplot(plot_user_rating_distribution(reviews_df))
    else:
        st.info("Log in to display your review history.")

    
