from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from alcopt.auth import (
    build_login_url,
    create_jwt,
    exchange_code,
    generate_state,
    get_user_info,
    is_admin,
)
from alcopt.api.dependencies import get_current_user, get_db
from alcopt.api.schemas import UserInfo
from alcopt.config import FRONTEND_URL
from alcopt.database.models import OAuthState

_SECURE_COOKIE = FRONTEND_URL.startswith("https")

router = APIRouter(prefix="/auth", tags=["auth"])

_STATE_TTL = timedelta(minutes=10)


def _cleanup_expired(db: Session):
    cutoff = datetime.now() - _STATE_TTL
    db.query(OAuthState).filter(OAuthState.created_at < cutoff).delete()


@router.get("/login")
def login(db: Session = Depends(get_db)):
    _cleanup_expired(db)
    state = generate_state()
    db.add(OAuthState(state=state, created_at=datetime.now()))
    db.commit()
    return {"url": build_login_url(state)}


@router.get("/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    row = db.get(OAuthState, state)
    if not row:
        return RedirectResponse(f"{FRONTEND_URL}?error=invalid_state")
    db.delete(row)
    db.commit()

    token_data = exchange_code(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(f"{FRONTEND_URL}?error=token_exchange_failed")

    user_info = get_user_info(token_data["access_token"])
    email = user_info.get("email", "") if user_info else ""
    picture = user_info.get("picture", "") if user_info else ""
    name = user_info.get("given_name", "") if user_info else ""

    jwt_token = create_jwt(email, picture, name)
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
        name=user.get("name", ""),
        is_admin=is_admin(user["email"]),
    )


@router.post("/logout")
def logout():
    response = Response(status_code=200)
    response.delete_cookie("token")
    return response
