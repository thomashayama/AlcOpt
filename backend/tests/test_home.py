from datetime import date

from tests.conftest import TestSession
from alcopt.database.models import (
    Container,
    Fermentation,
    ContainerFermentationLog,
    Review,
    SpecificGravityMeasurement,
)


def _seed_review_data():
    """Seed a container, fermentation, log, SG measurements, and reviews."""
    db = TestSession()
    container = Container(id=1, container_type="carboy")
    db.add(container)
    db.flush()

    ferm = Fermentation(id=1, start_date=date(2025, 1, 1))
    db.add(ferm)
    db.flush()

    from datetime import datetime

    log = ContainerFermentationLog(
        container_id=1, fermentation_id=1, start_date=datetime(2025, 1, 1)
    )
    db.add(log)

    db.add(
        SpecificGravityMeasurement(
            fermentation_id=1, measurement_date=date(2025, 1, 1), specific_gravity=1.090
        )
    )
    db.add(
        SpecificGravityMeasurement(
            fermentation_id=1, measurement_date=date(2025, 2, 1), specific_gravity=0.995
        )
    )

    db.add(
        Review(
            container_id=1,
            name="alice",
            fermentation_id=1,
            overall_rating=4.0,
            boldness=3.0,
            tannicity=2.5,
            sweetness=3.5,
            acidity=2.0,
            complexity=4.5,
            review_date=date(2025, 3, 1),
        )
    )
    db.add(
        Review(
            container_id=1,
            name="bob",
            fermentation_id=1,
            overall_rating=3.5,
            boldness=2.5,
            tannicity=3.0,
            sweetness=2.0,
            acidity=3.0,
            complexity=3.0,
            review_date=date(2025, 3, 2),
        )
    )
    db.commit()
    db.close()


def test_leaderboard_empty(client):
    resp = client.get("/api/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


def test_leaderboard_with_data(client):
    _seed_review_data()
    resp = client.get("/api/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    entry = data[0]
    assert entry["rank"] == 1
    assert entry["fermentation_id"] == 1
    assert entry["avg_rating"] == 3.75
    assert entry["num_ratings"] == 2


def test_analytics_reviews_empty(client):
    resp = client.get("/api/analytics/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


def test_analytics_reviews_with_data(client):
    _seed_review_data()
    resp = client.get("/api/analytics/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["overall_rating"] == 4.0


def test_analytics_ratings_abv(client):
    _seed_review_data()
    resp = client.get("/api/analytics/ratings-abv")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # ABV = (1.090 - 0.995) * 131.25 = 12.46875
    assert abs(data[0]["abv"] - 12.469) < 0.1


def test_analytics_ratings_rs(client):
    _seed_review_data()
    resp = client.get("/api/analytics/ratings-rs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # RS = (0.995 - 1) * 10000 = -50
    assert abs(data[0]["residual_sugar"] - (-50.0)) < 0.01
