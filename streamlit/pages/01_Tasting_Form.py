import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Tasting Form",
    page_icon="👋",
)

if "df" not in st.session_state:
    try:
        st.session_state.df = pd.read_csv("tasting.csv")
    except:
        st.session_state.df = pd.DataFrame()

with st.form("my_form"):
    name = st.text_input("Name")
    mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
    rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    bold = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    tannic = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    sweet = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    acidic = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
    complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)

    if st.form_submit_button('Submit'):
        st.session_state.df = st.session_state.df.append(
            {
                "mead_id": mead_id,
                "name": name,
                "rating": rating,
                "bold": bold,
                "tannic": tannic,
                "sweet": sweet,
                "acidic": acidic,
                "complexity": complexity
            }, 
            ignore_index=True
        )
        st.session_state.df.to_csv("data.csv")

st.dataframe(st.session_state.df, hide_index=True)
