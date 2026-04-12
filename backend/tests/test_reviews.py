from datetime import date, datetime

from tests.conftest import TestSession
from alcopt.database.models import Container, ContainerFermentationLog, Fermentation


def _seed_container_with_fermentation():
    db = TestSession()
    db.add(Container(id=1, container_type="bottle"))
    db.flush()
    db.add(Fermentation(id=1, start_date=date(2025, 1, 1)))
    db.flush()
    db.add(
        ContainerFermentationLog(
            container_id=1, fermentation_id=1, start_date=datetime(2025, 1, 1)
        )
    )
    db.commit()
    db.close()


def test_create_review(user_client):
    _seed_container_with_fermentation()
    resp = user_client.post(
        "/api/reviews",
        json={
            "container_id": 1,
            "tasting_date": "2025-06-01",
            "overall_rating": 4.0,
            "boldness": 3.0,
            "tannicity": 2.5,
            "sweetness": 3.5,
            "acidity": 2.0,
            "complexity": 4.5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["container_id"] == 1
    assert data["overall_rating"] == 4.0
    assert data["name"] == "user@test.com"
    assert data["fermentation_id"] == 1


def test_create_review_no_container(user_client):
    resp = user_client.post(
        "/api/reviews",
        json={
            "container_id": 999,
            "tasting_date": "2025-06-01",
            "overall_rating": 3.0,
            "boldness": 3.0,
            "tannicity": 3.0,
            "sweetness": 3.0,
            "acidity": 3.0,
            "complexity": 3.0,
        },
    )
    assert resp.status_code == 404


def test_create_review_no_fermentation(user_client):
    db = TestSession()
    db.add(Container(id=2, container_type="bottle"))
    db.commit()
    db.close()

    resp = user_client.post(
        "/api/reviews",
        json={
            "container_id": 2,
            "tasting_date": "2025-06-01",
            "overall_rating": 3.0,
            "boldness": 3.0,
            "tannicity": 3.0,
            "sweetness": 3.0,
            "acidity": 3.0,
            "complexity": 3.0,
        },
    )
    assert resp.status_code == 400


def test_create_review_invalid_rating(user_client):
    _seed_container_with_fermentation()
    resp = user_client.post(
        "/api/reviews",
        json={
            "container_id": 1,
            "tasting_date": "2025-06-01",
            "overall_rating": 6.0,  # out of range
            "boldness": 3.0,
            "tannicity": 3.0,
            "sweetness": 3.0,
            "acidity": 3.0,
            "complexity": 3.0,
        },
    )
    assert resp.status_code == 422


def test_create_review_unauthenticated(client):
    resp = client.post(
        "/api/reviews",
        json={
            "container_id": 1,
            "tasting_date": "2025-06-01",
            "overall_rating": 3.0,
            "boldness": 3.0,
            "tannicity": 3.0,
            "sweetness": 3.0,
            "acidity": 3.0,
            "complexity": 3.0,
        },
    )
    assert resp.status_code == 401


def test_my_reviews(user_client):
    _seed_container_with_fermentation()
    user_client.post(
        "/api/reviews",
        json={
            "container_id": 1,
            "tasting_date": "2025-06-01",
            "overall_rating": 4.0,
            "boldness": 3.0,
            "tannicity": 2.5,
            "sweetness": 3.5,
            "acidity": 2.0,
            "complexity": 4.5,
        },
    )
    resp = user_client.get("/api/reviews/mine")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "user@test.com"


def test_all_reviews_requires_admin(user_client):
    resp = user_client.get("/api/reviews")
    assert resp.status_code == 403


def test_all_reviews_as_admin(admin_client):
    resp = admin_client.get("/api/reviews")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
