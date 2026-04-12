"""Tests for the labels PDF endpoint."""


def test_generate_pdf(admin_client):
    resp = admin_client.get("/api/labels/pdf?min_id=1&max_id=4")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert b"%PDF" in resp.content


def test_generate_pdf_invalid_range(admin_client):
    resp = admin_client.get("/api/labels/pdf?min_id=10&max_id=5")
    assert resp.status_code == 400


def test_generate_pdf_requires_admin(user_client):
    resp = user_client.get("/api/labels/pdf?min_id=1&max_id=4")
    assert resp.status_code == 403


def test_generate_pdf_unauthenticated(client):
    resp = client.get("/api/labels/pdf?min_id=1&max_id=4")
    assert resp.status_code == 401
