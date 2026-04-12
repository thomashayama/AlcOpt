"""Tests for container CRUD and the composite info endpoint."""

from datetime import date, datetime

from tests.conftest import TestSession
from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    Fermentation,
    Ingredient,
    IngredientAddition,
    Review,
    SpecificGravityMeasurement,
)


def _seed_full_container():
    """Seed container 1 with fermentation, ingredients, SG, and reviews."""
    db = TestSession()
    db.add(
        Container(id=1, container_type="carboy", volume_liters=5.0, material="Glass")
    )
    db.add(
        Ingredient(
            id=1,
            name="Grape Juice",
            sugar_content=200.0,
            ingredient_type="Liquid",
            density=1.05,
        )
    )
    db.flush()

    db.add(Fermentation(id=1, start_date=date(2025, 1, 1)))
    db.flush()

    db.add(
        ContainerFermentationLog(
            container_id=1,
            fermentation_id=1,
            start_date=datetime(2025, 1, 1),
        )
    )
    db.add(
        IngredientAddition(
            container_id=1,
            ingredient_id=1,
            added_at=datetime(2025, 1, 1),
            amount=3000,
            unit="mL",
        )
    )
    db.add(
        SpecificGravityMeasurement(
            fermentation_id=1,
            measurement_date=date(2025, 1, 1),
            specific_gravity=1.090,
        )
    )
    db.add(
        SpecificGravityMeasurement(
            fermentation_id=1,
            measurement_date=date(2025, 2, 1),
            specific_gravity=0.995,
        )
    )
    db.add(
        Review(
            container_id=1,
            name="tester",
            fermentation_id=1,
            overall_rating=4.5,
            boldness=3.0,
            tannicity=2.5,
            sweetness=3.0,
            acidity=2.0,
            complexity=4.0,
            review_date=date(2025, 3, 1),
        )
    )
    db.commit()
    db.close()


# --- CRUD ---


def test_create_container(admin_client):
    resp = admin_client.post(
        "/api/containers",
        json={
            "container_type": "carboy",
            "volume_liters": 5.0,
            "material": "Glass",
            "empty_mass": 792.0,
            "date_added": "2025-01-01",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["container_type"] == "carboy"
    assert data["volume_liters"] == 5.0


def test_create_container_requires_admin(user_client):
    resp = user_client.post(
        "/api/containers",
        json={
            "container_type": "bottle",
        },
    )
    assert resp.status_code == 403


def test_list_containers(admin_client):
    db = TestSession()
    db.add(Container(container_type="carboy"))
    db.add(Container(container_type="bottle"))
    db.add(Container(container_type="bottle"))
    db.commit()
    db.close()

    resp = admin_client.get("/api/containers")
    assert len(resp.json()) == 3

    resp = admin_client.get("/api/containers?container_type=bottle")
    assert len(resp.json()) == 2


# --- Container Info (public) ---


def test_container_info(client):
    _seed_full_container()
    resp = client.get("/api/containers/1")
    assert resp.status_code == 200
    data = resp.json()

    # Container details
    assert data["container"]["container_type"] == "carboy"
    assert data["container"]["volume_liters"] == 5.0

    # Fermentation
    assert data["fermentation"]["id"] == 1

    # Ingredients
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["ingredient"] == "Grape Juice"

    # SG measurements
    assert len(data["sg_measurements"]) == 2

    # ABV calculated from SG diff
    assert data["abv"] is not None
    expected_abv = (1.090 - 0.995) * 131.25
    assert abs(data["abv"] - expected_abv) < 0.01

    # Residual sugar
    assert data["residual_sugar"] is not None

    # Reviews
    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["overall_rating"] == 4.5


def test_container_info_not_found(client):
    resp = client.get("/api/containers/999")
    assert resp.status_code == 404


def test_container_info_no_fermentation(client):
    db = TestSession()
    db.add(Container(id=1, container_type="bottle"))
    db.commit()
    db.close()

    resp = client.get("/api/containers/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fermentation"] is None
    assert data["abv"] is None
    assert data["ingredients"] == []
    assert data["sg_measurements"] == []


def test_container_info_one_sg(client):
    """With only 1 SG measurement, ABV should be null."""
    db = TestSession()
    db.add(Container(id=1, container_type="carboy"))
    db.flush()
    db.add(Fermentation(id=1, start_date=date(2025, 1, 1)))
    db.flush()
    db.add(
        ContainerFermentationLog(
            container_id=1,
            fermentation_id=1,
            start_date=datetime(2025, 1, 1),
        )
    )
    db.add(
        SpecificGravityMeasurement(
            fermentation_id=1,
            measurement_date=date(2025, 1, 1),
            specific_gravity=1.090,
        )
    )
    db.commit()
    db.close()

    resp = client.get("/api/containers/1")
    data = resp.json()
    assert data["abv"] is None
    assert data["residual_sugar"] is None
