import requests
import streamlit as st
from streamlit_oauth import OAuth2Component
from datetime import datetime, timedelta

from alcopt.config import (
    GOOGLE_AUTHORIZE_URL, GOOGLE_TOKEN_URL, GOOGLE_REFRESH_TOKEN_URL,
    GOOGLE_REVOKE_TOKEN_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI, GOOGLE_SCOPE, ADMIN_EMAILS,
)

# Initialize OAuth2
oauth2 = OAuth2Component(
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GOOGLE_AUTHORIZE_URL, GOOGLE_TOKEN_URL,
    GOOGLE_REFRESH_TOKEN_URL, GOOGLE_REVOKE_TOKEN_URL,
)

def logout():
    """Clear user session and refresh."""
    if "token" in st.session_state:
        del st.session_state["token"]  # Remove stored token
    if "profile_pic" in st.session_state:
        del st.session_state["profile_pic"]  # Clear profile pic if stored
    st.rerun()  # Rerun app to reflect logout state

def show_login_status():
    """Display login button or user profile in the sidebar"""

    with st.sidebar:
        st.markdown(
            """
            <style>
                .profile-img {
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                }
                .logout-button {
                    border: none;
                    background: none;
                    color: red;
                    cursor: pointer;
                    font-size: 16px;
                    padding: 5px;
                }
            </style>
            <div class="header-container">
        """,
            unsafe_allow_html=True,
        )

        token = get_user_token()

        if token:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center;">
                    <img src="{st.session_state.profile_pic}" class="profile-img">
                    <form action="" method="post">
                        <input type="submit" value="Logout" name="logout" class="logout-button">
                    </form>
                </div>
                </div> <!-- End of header-container -->
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("logout"):
                # del st.session_state["token"]
                logout()
                st.markdown('<meta http-equiv="refresh" content="0;URL=/alcopt">', unsafe_allow_html=True)

    return token

def get_user_token(button_key="login"):
    """Handles OAuth2 login and returns the token."""
    if "token" not in st.session_state:
        result = oauth2.authorize_button("Login with Google", GOOGLE_REDIRECT_URI, GOOGLE_SCOPE, key=button_key)
        if result and "token" in result:
            st.session_state.token = result["token"]
            user_info = get_user_info(st.session_state["token"]["access_token"])
            if user_info:
                st.session_state.user_email = user_info.get("email", "Unknown User")
                st.session_state.user_id = user_info.get("id", 0)
                st.session_state.profile_pic = user_info.get("picture", "https://via.placeholder.com/50")
            else:
                st.session_state.profile_pic = "https://via.placeholder.com/50"
            st.rerun()
    return st.session_state.get("token")

def refresh_access_token():
    if "token" not in st.session_state:
        return False

    token = oauth2.refresh_token(
        refresh_token=st.session_state["token"],
    )

    st.session_state["token"] = token
    return True

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

def is_admin():
    """Checks if current user is admin"""
    return st.session_state.user_email in ADMIN_EMAILS
