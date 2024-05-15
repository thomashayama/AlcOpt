import streamlit as st
import pandas as pd
import numpy as np

if "df" not in st.session_state:
    st.session_state.df = pd.read_csv("data.csv")

# df = st.session_state.df

# if st.button('Submit'):
#     st.session_state.df = get_data()

with st.form("my_form"):
    rating = st.slider("Overall Rating", min_value=1, max_value=10)
    bold = st.slider("Light to Bold", min_value=1, max_value=10)
    tannic = st.slider("Smooth to Tannic", min_value=1, max_value=10)
    sweet = st.slider("Dry to Sweet", min_value=1, max_value=10)
    acidic = st.slider("Soft to Acidic", min_value=1, max_value=10)
    complex = st.slider("Simple to Complex", min_value=1, max_value=10)

    if st.form_submit_button('Submit'):
        print("hi")
