import streamlit as st
import pandas as pd

import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

from sqlalchemy.orm import Session
from sqlalchemy import func

from alcopt.database.models import Fermentation, Review
from alcopt.database.queries import get_fermentation_leaderboard
from alcopt.database.utils import init_db, get_db

st.set_page_config(
    page_title="Home",
    page_icon="👋",
)

init_db()

st.markdown(
    """
    Web App for recording tastings, brewing information, and tracking bottling.
"""
)

st.page_link("pages/01_Tasting_Form.py", label="Tasting Form", icon="1️⃣")
st.page_link("pages/02_Brew_Log.py", label="Brew Logging", icon="2️⃣")
st.page_link("pages/03_Bottle_Log.py", label="Bottle Logging", icon="2️⃣")

# Mead Average Ratings in a Leaderboard
st.markdown("## Mead Leaderboard")
st.title("Fermentation Leaderboard")

with get_db() as db:
    leaderboard_df = get_fermentation_leaderboard(db)
    st.dataframe(leaderboard_df, hide_index=True)

# Plots
st.markdown("## Plots")
fig = plt.figure() 
plt.plot([1, 2, 3, 4, 5]) 

st.pyplot(fig)