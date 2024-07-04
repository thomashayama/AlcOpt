import streamlit as st
import pandas as pd

# SQL
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

from alcopt.sqlalchemy_models import Fermentation, Bottle, Review, Vessel
from alcopt.streamlit_utils import all_vessels_info, all_bottle_info

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
        volume_liters = st.number_input("Volume (L)", value=2.000, min_value=0.00)
        empty_mass = st.number_input("Empty Mass (g)", value=792.0, min_value=0.00)
        vessel_button = st.form_submit_button('Submit')

    session = Session()
    if vessel_button:
        new_vessel = Vessel(volume_liters=volume_liters, material=material, empty_mass=empty_mass, date_added=date)
        session.add(new_vessel)
        session.commit()
        st.success("Vessel added successfully!")
    
    st.dataframe(all_vessels_info(session), use_container_width=True, hide_index=True)
    session.close()

with tab_new_bottle:
    with st.form(key="new_bottle"):
        date = st.date_input("Date Added")
        volume_liters = st.number_input("Volume (L)", value=0.500, min_value=0.00)
        empty_mass = st.number_input("Empty Mass (g)", value=500.0, min_value=0.00)
        bottle_button = st.form_submit_button('Submit')
    
    session = Session()
    if bottle_button:
        new_bottle = Bottle(volume_liters=volume_liters, empty_mass=empty_mass, date_added=date)
        session.add(new_bottle)
        session.commit()
        st.success("Bottle added successfully!")
    
    st.dataframe(all_bottle_info(session), hide_index=True)
    session.close()