from alcopt.auth import create_jwt, decode_jwt, is_admin


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


def test_logout(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
