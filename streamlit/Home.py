import streamlit as st

import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Home",
    page_icon="👋",
)

st.markdown(
    """
    Web App for recording tastings, brewing information, and tracking bottling.
"""
)

st.page_link("pages/01_Tasting_Form.py", label="Tasting Form", icon="1️⃣")
st.page_link("pages/02_Brew_Log.py", label="Brew Logging", icon="2️⃣")
st.page_link("pages/03_Bottle_Log.py", label="Bottle Logging", icon="2️⃣")


conn = st.connection('alcohol_db', type='sql')
# Mead Average Ratings in a Leaderboard
st.markdown("## Mead Leaderboard")
tasting_table = conn.query("SELECT mead_id, AVG(rating) AS avg_rating, COUNT(mead_id) AS num_reviews FROM tasting GROUP BY mead_id ORDER BY avg_rating DESC;")
tasting_table = tasting_table.rename(columns={"mead_id": "Mead ID", "avg_rating": "Avg Rating", "num_reviews": "# Reviews"})
st.dataframe(tasting_table, use_container_width=False, hide_index=True)

# Plots
st.markdown("## Plots")
fig = plt.figure() 
plt.plot([1, 2, 3, 4, 5]) 

st.pyplot(fig)