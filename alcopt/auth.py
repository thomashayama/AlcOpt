import requests
import streamlit as st
from streamlit_oauth import OAuth2Component

# OAuth2 Configuration
AUTHORIZE_URL = st.secrets["oauth"]["google"]["AUTHORIZE_URL"]
TOKEN_URL = st.secrets["oauth"]["google"]["TOKEN_URL"]
REFRESH_TOKEN_URL = st.secrets["oauth"]["google"]["REFRESH_TOKEN_URL"]
REVOKE_TOKEN_URL = st.secrets["oauth"]["google"]["REVOKE_TOKEN_URL"]
CLIENT_ID = st.secrets["oauth"]["google"]["CLIENT_ID"]
CLIENT_SECRET = st.secrets["oauth"]["google"]["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["oauth"]["google"]["REDIRECT_URI"]
SCOPE = st.secrets["oauth"]["google"]["SCOPE"]

# Initialize OAuth2
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)

def get_user_token():
    """Handles OAuth2 login and returns the token."""
    if "token" not in st.session_state:
        result = oauth2.authorize_button("Login with Google", REDIRECT_URI, SCOPE)
        if result and "token" in result:
            st.session_state.token = result["token"]
            user_info = get_user_info(st.session_state["token"]["access_token"])
            if user_info:
                st.session_state.user_email = user_info.get("email")
                st.session_state.user_id = user_info.get("id")
                print(st.session_state.user_email)
            st.rerun()
    return st.session_state.get("token")

def get_user_info(token):
    """Fetch user info from Google OAuth2."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
    return response.json() if response.status_code == 200 else None

def logout():
    """Removes token and logs the user out."""
    if "token" in st.session_state:
        del st.session_state["token"]
    st.rerun()

def show_login_status():
    """Shows login status and login/logout button in the sidebar."""
    with st.sidebar:
        if "token" in st.session_state:
            st.write("✅ Logged in")
            if st.button("Logout"):
                logout()
        else:
            get_user_token()
