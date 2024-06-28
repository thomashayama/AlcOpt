import streamlit as st

# SQL
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy_models import Fermentation, Bottle, Review, Vessel

st.set_page_config(
    page_title="Bottle Tracking",
)

# Create the SQL connection to pets_db as specified in your secrets file.
# conn = st.connection('alcohol_db', type='sql')
engine = create_engine('sqlite:///wine_mead.db')
Session = sessionmaker(bind=engine)

if "last_data" not in st.session_state:
    st.session_state.last_data = {}

tab_new_vessel, tab_new_bottle = st.tabs(["New Vessel", "New Bottle"])
with tab_new_vessel:
    with st.form(key="new_vessel"):
        date = st.date_input("Date Added")
        material = st.text_input("Material", value="Glass")
        capacity_liters = st.number_input("Capacity (L)", value=1.750, min_value=0.00)

        if st.form_submit_button('Submit'):
            session = Session()
            new_vessel = Vessel(capacity_liters=capacity_liters, material=material)
            session.add(new_vessel)
            session.commit()
            session.close()
            st.success("Vessel added successfully!")
with tab_new_bottle:
    with st.form(key="new_bottle"):
        date = st.date_input("Date Added")
        volume_liters = st.number_input("Volume (L)", value=0.750, min_value=0.00)

        if st.form_submit_button('Submit'):
            session = Session()
            new_bottle = Bottle(volume_liters=volume_liters)
            session.add(new_bottle)
            session.commit()
            session.close()
            st.success("Bottle added successfully!")