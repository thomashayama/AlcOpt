"""Entry point and navigation router for AlcOpt.

Builds the page list dynamically based on the current user's auth state,
so admin-only pages are hidden from the sidebar entirely (not just gated
on click). Each page module is run in turn by st.navigation.run().
"""

import logging

import streamlit as st

from alcopt.auth import is_admin, show_login_status
from alcopt.database.utils import init_db

st.set_page_config(
    page_title="AlcOpt",
    page_icon="🍷",
    layout="centered",
    initial_sidebar_state="expanded",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

init_db()
token = show_login_status()

public_pages = [
    st.Page(
        "pages/00_Home.py",
        title="Home",
        icon=":material/home:",
        default=True,
    ),
    st.Page(
        "pages/01_Tasting_Form.py",
        title="Tasting Form",
        icon=":material/rate_review:",
    ),
    st.Page(
        "pages/04_Information.py",
        title="Information",
        icon=":material/info:",
    ),
]

admin_pages = [
    st.Page(
        "pages/02_Brew_Log.py",
        title="Brew Log",
        icon=":material/science:",
    ),
    st.Page(
        "pages/03_Bottle_Log.py",
        title="Bottle Log",
        icon=":material/wine_bar:",
    ),
    st.Page(
        "pages/05_Container_Labels.py",
        title="Container Labels",
        icon=":material/qr_code:",
    ),
]

pages = public_pages + (admin_pages if token and is_admin() else [])
st.navigation(pages).run()
