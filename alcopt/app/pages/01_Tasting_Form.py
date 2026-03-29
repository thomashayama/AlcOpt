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
    boldness = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1, help="""A bold wine is typically full-bodied, high in tannins, and has strong flavors that linger. It often has higher alcohol content and a more pronounced texture, making it feel heavier in the mouth. Examples include Cabernet Sauvignon, Malbec, and Syrah.
        On the other hand, a light wine is more delicate, with subtle flavors and a lower perception of weight on the palate. Light wines tend to have lower tannins, higher acidity, and a refreshing quality. They are often fruit-forward and easier to drink, making them versatile with food pairings. Examples include Pinot Noir, Gamay, and Riesling.""")
    tannicity = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1, help="""A smooth wine has soft, well-integrated tannins, creating a velvety, easy-drinking experience. It glides across the tongue without astringency or harshness, often with a round and supple mouthfeel. Smooth wines are typically aged longer, allowing tannins to mellow, or they naturally have lower tannin levels. Examples include Merlot, Pinot Noir, and aged Bordeaux blends.
        A tannic wine, on the other hand, has a firm, grippy structure due to higher levels of tannins—compounds found in grape skins, seeds, and oak aging. Tannins create a drying sensation in the mouth, similar to strong black tea. These wines can feel bold and structured, often benefiting from aging to soften their texture over time. Examples include young Cabernet Sauvignon, Nebbiolo, and Syrah.""")
    sweetness = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1, help="""A dry wine has little to no residual sugar, meaning all or most of the grape’s natural sugars have been converted into alcohol. These wines do not taste sweet but may still have fruit-forward flavors. Dry wines can range from crisp and refreshing (like Sauvignon Blanc) to bold and tannic (like Cabernet Sauvignon).
        A sweet wine retains some of its natural sugars, giving it a noticeable sweetness on the palate. Sweet wines can range from lightly off-dry (like Riesling) to lusciously rich and dessert-like (such as Sauternes or Port). The sweetness can be balanced by acidity to keep the wine lively rather than cloying.""")
    acidity = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1, help="""A soft wine has lower acidity, creating a round, mellow, and smooth mouthfeel. It lacks sharpness or tartness and tends to feel plush and easy-drinking. Soft wines often emphasize ripe fruit flavors and have a gentle finish. Examples include Merlot, Viognier, and oaked Chardonnay.
        An acidic wine has a bright, crisp, and zesty character due to higher acidity. Acidity gives wine a lively, refreshing quality and enhances its ability to pair with food. It can create a tingling sensation on the tongue and make the mouth water. High-acid wines, like Sauvignon Blanc, Riesling, and Pinot Noir, tend to taste more vibrant and structured.""")
    complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1, help="""A simple wine has straightforward, easily identifiable flavors that don’t change much from the first sip to the finish. It is typically fruit-forward and easy to drink, with a clean and consistent profile. Simple wines can still be enjoyable and refreshing, often making them great for casual drinking. Examples include young Pinot Grigio, Beaujolais Nouveau, and some unoaked Chardonnays.
        A complex wine, on the other hand, offers multiple layers of flavors and aromas that evolve over time in the glass. It may have a mix of fruit, spice, earth, floral, and oak characteristics that change as you sip, revealing new nuances. Complex wines often have longer finishes and develop more character as they age. Examples include aged Bordeaux, Burgundy, and fine Barolo.""")

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

    
