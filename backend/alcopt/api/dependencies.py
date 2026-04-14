from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from alcopt.auth import decode_jwt, is_admin
from alcopt.database.models import RevokedToken
from alcopt.database.utils import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _is_revoked(db: Session, jti: str | None) -> bool:
    if not jti:
        return False
    return db.get(RevokedToken, jti) is not None


def get_current_user(
    token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if _is_revoked(db, payload.get("jti")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token revoked")
    return {
        "email": payload["sub"],
        "picture": payload.get("picture", ""),
        "name": payload.get("name", ""),
        "jti": payload.get("jti"),
        "exp": payload.get("exp"),
    }


def get_optional_user(
    token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    if not token:
        return None
    payload = decode_jwt(token)
    if not payload:
        return None
    if _is_revoked(db, payload.get("jti")):
        return None
    return {
        "email": payload["sub"],
        "picture": payload.get("picture", ""),
        "name": payload.get("name", ""),
        "jti": payload.get("jti"),
        "exp": payload.get("exp"),
    }


def require_admin(user: dict = Depends(get_current_user)):
    if not is_admin(user["email"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
