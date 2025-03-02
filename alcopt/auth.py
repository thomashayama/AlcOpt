def authenticate_user(username, password):
    users = {
        "user1": {"password": "userpass", "role": "user"},
        "admin1": {"password": "adminpass", "role": "admin"}
    }
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def get_user_role():
    """Returns the role of the currently logged-in user."""
    return st.session_state.get("role")