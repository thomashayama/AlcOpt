from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from alcopt.auth import (
    build_login_url,
    create_jwt,
    exchange_code,
    generate_state,
    get_user_info,
    is_admin,
)
from alcopt.api.dependencies import get_current_user
from alcopt.api.schemas import UserInfo
from alcopt.config import FRONTEND_URL

_SECURE_COOKIE = FRONTEND_URL.startswith("https")

router = APIRouter(prefix="/auth", tags=["auth"])

_pending_states: dict[str, bool] = {}


@router.get("/login")
def login():
    state = generate_state()
    _pending_states[state] = True
    return {"url": build_login_url(state)}


@router.get("/callback")
def callback(code: str, state: str):
    if state not in _pending_states:
        return RedirectResponse(f"{FRONTEND_URL}?error=invalid_state")
    del _pending_states[state]

    token_data = exchange_code(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(f"{FRONTEND_URL}?error=token_exchange_failed")

    user_info = get_user_info(token_data["access_token"])
    email = user_info.get("email", "") if user_info else ""
    picture = user_info.get("picture", "") if user_info else ""

    jwt_token = create_jwt(email, picture)
    response = RedirectResponse(FRONTEND_URL)
    response.set_cookie(
        "token",
        jwt_token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return response


@router.get("/me", response_model=UserInfo)
def me(user: dict = Depends(get_current_user)):
    return UserInfo(
        email=user["email"],
        picture=user["picture"],
        is_admin=is_admin(user["email"]),
    )


@router.post("/logout")
def logout():
    response = Response(status_code=200)
    response.delete_cookie("token")
    return response
