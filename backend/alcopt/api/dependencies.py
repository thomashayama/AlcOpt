from fastapi import Cookie, Depends, HTTPException, status

from alcopt.auth import decode_jwt, is_admin
from alcopt.database.utils import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str | None = Cookie(None)):
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return {"email": payload["sub"], "picture": payload.get("picture", "")}


def get_optional_user(token: str | None = Cookie(None)):
    if not token:
        return None
    payload = decode_jwt(token)
    if not payload:
        return None
    return {"email": payload["sub"], "picture": payload.get("picture", "")}


def require_admin(user: dict = Depends(get_current_user)):
    if not is_admin(user["email"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
