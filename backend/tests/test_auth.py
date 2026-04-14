from datetime import datetime, timedelta

from alcopt.auth import create_jwt, decode_jwt, is_admin
from alcopt.database.models import RevokedToken
from tests.conftest import TestSession


def test_create_and_decode_jwt():
    token = create_jwt("test@example.com", "pic.jpg")
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["picture"] == "pic.jpg"


def test_decode_invalid_jwt():
    assert decode_jwt("garbage.token.here") is None
    assert decode_jwt("") is None


def test_is_admin(monkeypatch):
    monkeypatch.setattr("alcopt.auth.ADMIN_EMAILS", ["admin@test.com"])
    assert is_admin("admin@test.com") is True
    assert is_admin("user@test.com") is False
    assert is_admin("") is False


def test_login_returns_url(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "accounts.google.com" in data["url"]


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_authenticated(user_client):
    resp = user_client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "user@test.com"


def test_logout(user_client):
    resp = user_client.post("/auth/logout")
    assert resp.status_code == 200


def test_logout_unauthenticated(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 401


def test_jwt_contains_jti():
    token = create_jwt("test@example.com")
    payload = decode_jwt(token)
    assert payload is not None
    assert "jti" in payload
    assert len(payload["jti"]) > 0


def test_revoked_jti_rejects_requests(client):
    """A JWT whose jti is in RevokedToken should be treated as unauthenticated."""
    token = create_jwt("user@test.com")
    payload = decode_jwt(token)

    db = TestSession()
    db.add(
        RevokedToken(
            jti=payload["jti"],
            expires_at=datetime.now() + timedelta(hours=1),
        )
    )
    db.commit()
    db.close()

    resp = client.get("/auth/me", cookies={"token": token})
    assert resp.status_code == 401
