import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Tasting Form",
    page_icon="👋",
)

if "df" not in st.session_state:
    try:
        st.session_state.df = pd.read_csv("data.csv")
    except:
        st.session_state.df = pd.DataFrame()

with st.form("my_form"):
    name = st.text_input("Name")
    mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
    rating = st.slider("Overall Rating", min_value=1, max_value=10)
    bold = st.slider("Light to Bold", min_value=1, max_value=10)
    tannic = st.slider("Smooth to Tannic", min_value=1, max_value=10)
    sweet = st.slider("Dry to Sweet", min_value=1, max_value=10)
    acidic = st.slider("Soft to Acidic", min_value=1, max_value=10)
    complex = st.slider("Simple to Complex", min_value=1, max_value=10)

    if st.form_submit_button('Submit'):
        st.session_state.df = st.session_state.df.append(
            {
                "name": name,
                "rating": rating,
                "bold": bold,
                "tannic": tannic,
                "sweet": sweet,
                "acidic": acidic,
                "complex": complex
            }, 
            ignore_index=True
        )

st.dataframe(st.session_state.df, hide_index=True)
