import streamlit as st
import pandas as pd

from alcopt.database.models import Fermentation, Bottle, Review, Vessel
from alcopt.database.utils import get_db
from alcopt.streamlit_utils import all_vessels_info, all_bottle_info
from alcopt.auth import get_user_token, show_login_status, is_admin

st.set_page_config(
    page_title="Bottle Tracking",
    page_icon="🍷",
)

# Show login/logout button
token = show_login_status()

if not token:
    st.warning("🔒 Please log in to access this page.")
    st.stop()

if "last_data" not in st.session_state:
    st.session_state.last_data = {}

if is_admin():
    tab_new_vessel, tab_new_bottle = st.tabs(["New Vessel", "New Bottle"])
    with tab_new_vessel:
        with st.form(key="new_vessel"):
            date = st.date_input("Date Added")
            material = st.text_input("Material", value="Glass")
            volume_liters = st.number_input("Volume (L)", value=2.000, min_value=0.00)
            empty_mass = st.number_input("Empty Mass (g)", value=792.0, min_value=0.00)
            vessel_button = st.form_submit_button('Submit')

        with get_db() as db:
            if vessel_button:
                new_vessel = Vessel(volume_liters=volume_liters, material=material, empty_mass=empty_mass, date_added=date)
                db.add(new_vessel)
                db.commit()
                st.success("Vessel added successfully!")
            
            st.dataframe(all_vessels_info(db), use_container_width=True, hide_index=True)

    with tab_new_bottle:
        with st.form(key="new_bottle"):
            date = st.date_input("Date Added")
            volume_liters = st.number_input("Volume (L)", value=0.500, min_value=0.00)
            empty_mass = st.number_input("Empty Mass (g)", value=500.0, min_value=0.00)
            bottle_button = st.form_submit_button('Submit')
        
        with get_db() as db:
            if bottle_button:
                new_bottle = Bottle(volume_liters=volume_liters, empty_mass=empty_mass, date_added=date)
                db.add(new_bottle)
                db.commit()
                st.success("Bottle added successfully!")
            
            st.dataframe(all_bottle_info(db), hide_index=True)
else:
    st.error("🔒Admin Page")