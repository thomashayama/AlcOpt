import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Tasting Form",
    page_icon="🍷",
)

# Create the SQL connection to pets_db as specified in your secrets file.
conn = st.connection('alcohol_db', type='sql')

if "df" not in st.session_state:
    try:
        st.session_state.df = pd.read_csv("../data/tasting.csv")
    except:
        st.session_state.df = pd.DataFrame()
if "page_state" not in st.session_state:
    st.session_state.page_state = 0
if "last_data" not in st.session_state:
    st.session_state.last_data = {}

conn.session.execute("""
                     CREATE TABLE IF NOT EXISTS tasting 
                     (
                        mead_id int, 
                        name varchar(255) NOT NULL, 
                        taste_date date,
                        rating float(2), 
                        bold float(2), 
                        tannic float(2), 
                        sweet float(2), 
                        acidic float(2), 
                        complexity float(2)
                     )
                     """)

if st.session_state.page_state == 0:
    with st.form("Tasting Form"):
        name = st.text_input("Full Name", placeholder=st.session_state.last_data.get("name", "John Doe"), autocomplete="on")
        mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
        date = st.date_input("Tasting Date")
        rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        bold = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        tannic = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        sweet = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        acidic = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)

        if st.form_submit_button('Submit'):
            # Insert some data with conn.session.
            with conn.session as s:
                s.execute(f"""INSERT INTO tasting VALUES 
                        ({mead_id}, '{name}', '{date}', {rating}, {bold}, {tannic}, {sweet}, {acidic}, {complexity});""")
                s.commit()
            print(f"Submitted {mead_id}, '{name}', '{date}', {rating}, {bold}, {tannic}, {sweet}, {acidic}, {complexity}")
            st.session_state.page_state = 1
            st.session_state.last_data["name"] = name

            st.rerun()

    conn.reset()
    tasting_table = conn.query("SELECT * FROM tasting ORDER BY taste_date DESC;")
    st.dataframe(tasting_table, use_container_width=True, hide_index=True)
elif st.session_state.page_state == 1:
    st.markdown("Form Submitted")

    if st.button("Submit Another"):
        st.session_state.page_state = 0
        st.rerun()
        
