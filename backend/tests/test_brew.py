"""Tests for brew router — fermentation lifecycle, ingredients, measurements, rack, bottle."""

from datetime import date, datetime

from tests.conftest import TestSession
from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    Fermentation,
    Ingredient,
)


def _seed_containers():
    db = TestSession()
    db.add(Container(id=1, container_type="carboy", volume_liters=5.0))
    db.add(Container(id=2, container_type="carboy", volume_liters=5.0))
    db.add(Container(id=3, container_type="bottle", volume_liters=0.75))
    db.commit()
    db.close()


def _seed_container_with_fermentation():
    """Seed container 1 with an active fermentation."""
    _seed_containers()
    db = TestSession()
    db.add(Fermentation(id=1, start_date=date(2025, 1, 1)))
    db.flush()
    db.add(
        ContainerFermentationLog(
            container_id=1,
            fermentation_id=1,
            start_date=datetime(2025, 1, 1),
            stage="primary",
        )
    )
    db.commit()
    db.close()


def _seed_ingredient():
    db = TestSession()
    db.add(
        Ingredient(
            id=1,
            name="Grape Juice",
            sugar_content=200.0,
            ingredient_type="Liquid",
            density=1.05,
            price=5.0,
        )
    )
    db.commit()
    db.close()


# --- Auth ---


def test_brew_requires_admin(user_client):
    resp = user_client.get("/api/brew/fermentations")
    assert resp.status_code == 403


def test_brew_unauthenticated(client):
    resp = client.get("/api/brew/fermentations")
    assert resp.status_code == 401


# --- Start Fermentation ---


def test_start_fermentation(admin_client):
    _seed_containers()
    resp = admin_client.post(
        "/api/brew/fermentations",
        json={
            "container_id": 1,
            "start_date": "2025-01-01",
            "stage": "primary",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["container_id"] == 1
    assert data["stage"] == "primary"
    assert data["fermentation_id"] == 1


def test_start_fermentation_nonexistent_container(admin_client):
    resp = admin_client.post(
        "/api/brew/fermentations",
        json={
            "container_id": 999,
            "start_date": "2025-01-01",
            "stage": "primary",
        },
    )
    assert resp.status_code == 404


def test_start_fermentation_closes_previous(admin_client):
    _seed_containers()
    # Start first fermentation
    admin_client.post(
        "/api/brew/fermentations",
        json={
            "container_id": 1,
            "start_date": "2025-01-01",
            "stage": "primary",
        },
    )
    # Start second on same container — should close the first
    resp = admin_client.post(
        "/api/brew/fermentations",
        json={
            "container_id": 1,
            "start_date": "2025-06-01",
            "stage": "primary",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["fermentation_id"] == 2

    # Verify first log is closed
    db = TestSession()
    logs = db.query(ContainerFermentationLog).filter_by(container_id=1).all()
    assert len(logs) == 2
    assert logs[0].end_date is not None  # first closed
    assert logs[1].end_date is None  # second open
    db.close()


def test_list_fermentation_logs(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.get("/api/brew/fermentations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


# --- Ingredients ---


def test_create_ingredient(admin_client):
    resp = admin_client.post(
        "/api/brew/ingredients",
        json={
            "name": "Honey",
            "sugar_content": 800.0,
            "ingredient_type": "Liquid",
            "density": 1.4,
            "price": 12.0,
            "notes": "wildflower",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Honey"
    assert data["sugar_content"] == 800.0


def test_list_ingredients(admin_client):
    _seed_ingredient()
    resp = admin_client.get("/api/brew/ingredients")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Grape Juice"


# --- Ingredient Additions ---


def test_add_ingredient_addition(admin_client):
    _seed_container_with_fermentation()
    _seed_ingredient()
    resp = admin_client.post(
        "/api/brew/additions",
        json={
            "container_id": 1,
            "ingredient_name": "Grape Juice",
            "date": "2025-01-02",
            "starting_amount": 0.0,
            "ending_amount": 1000.0,
            "unit": "mL",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["fermentation_id"] == 1
    assert "id" in data


def test_add_ingredient_nonexistent_ingredient(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/additions",
        json={
            "container_id": 1,
            "ingredient_name": "Nonexistent",
            "date": "2025-01-02",
            "starting_amount": 0.0,
            "ending_amount": 500.0,
            "unit": "g",
        },
    )
    assert resp.status_code == 404


def test_add_ingredient_no_fermentation(admin_client):
    """Adding to container with no active fermentation should still work (returns null ferm)."""
    _seed_containers()
    _seed_ingredient()
    resp = admin_client.post(
        "/api/brew/additions",
        json={
            "container_id": 1,
            "ingredient_name": "Grape Juice",
            "date": "2025-01-02",
            "starting_amount": 0.0,
            "ending_amount": 500.0,
            "unit": "g",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fermentation_id"] is None


def test_list_additions(admin_client):
    resp = admin_client.get("/api/brew/additions")
    assert resp.status_code == 200


# --- SG Measurements ---


def test_add_sg_measurement(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "specific_gravity": 1.090,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["specific_gravity"] == 1.090
    assert data["fermentation_id"] == 1


def test_add_sg_no_fermentation(admin_client):
    _seed_containers()
    resp = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "specific_gravity": 1.050,
        },
    )
    assert resp.status_code == 400


# --- Mass Measurements ---


def test_add_mass_measurement(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/mass-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "mass": 5200.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mass"] == 5200.0


def test_add_mass_no_fermentation(admin_client):
    _seed_containers()
    resp = admin_client.post(
        "/api/brew/mass-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "mass": 5000.0,
        },
    )
    assert resp.status_code == 400


# --- Rack ---


def test_rack(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/rack",
        json={
            "from_container_id": 1,
            "to_container_id": 2,
            "date": "2025-02-01",
            "stage": "secondary",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["container_id"] == 2
    assert data["fermentation_id"] == 1
    assert data["source_container_id"] == 1
    assert data["stage"] == "secondary"

    # Verify source log is closed
    db = TestSession()
    source_log = db.query(ContainerFermentationLog).filter_by(container_id=1).first()
    assert source_log.end_date is not None
    db.close()


def test_rack_no_source_fermentation(admin_client):
    _seed_containers()
    resp = admin_client.post(
        "/api/brew/rack",
        json={
            "from_container_id": 1,
            "to_container_id": 2,
            "date": "2025-02-01",
            "stage": "secondary",
        },
    )
    assert resp.status_code == 400


def test_rack_nonexistent_container(admin_client):
    resp = admin_client.post(
        "/api/brew/rack",
        json={
            "from_container_id": 999,
            "to_container_id": 1,
            "date": "2025-02-01",
            "stage": "secondary",
        },
    )
    assert resp.status_code == 404


# --- Bottle ---


def test_bottle(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/bottle",
        json={
            "from_container_id": 1,
            "to_container_id": 3,
            "date": "2025-03-01",
            "amount": 750.0,
            "unit": "mL",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["container_id"] == 3
    assert data["fermentation_id"] == 1
    assert data["amount"] == 750.0
    assert data["stage"] == "bottled"

    # Verify source log is NOT closed (bottle doesn't close source)
    db = TestSession()
    source_log = db.query(ContainerFermentationLog).filter_by(container_id=1).first()
    assert source_log.end_date is None
    db.close()


def test_bottle_no_source_fermentation(admin_client):
    _seed_containers()
    resp = admin_client.post(
        "/api/brew/bottle",
        json={
            "from_container_id": 1,
            "to_container_id": 3,
            "date": "2025-03-01",
            "amount": 750.0,
            "unit": "mL",
        },
    )
    assert resp.status_code == 400


# --- Empty ---


def test_empty_container(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post("/api/brew/empty/1")
    assert resp.status_code == 200
    assert "emptied" in resp.json()["message"]

    db = TestSession()
    log = db.query(ContainerFermentationLog).filter_by(container_id=1).first()
    assert log.end_date is not None
    db.close()


def test_empty_no_open_log(admin_client):
    _seed_containers()
    resp = admin_client.post("/api/brew/empty/1")
    assert resp.status_code == 200
    assert "no open log" in resp.json()["message"]


def test_empty_nonexistent(admin_client):
    resp = admin_client.post("/api/brew/empty/999")
    assert resp.status_code == 404


# --- Full Lifecycle ---


def test_full_fermentation_lifecycle(admin_client):
    """Start -> Add ingredients -> SG measurements -> Rack -> Bottle -> Review."""
    _seed_containers()
    _seed_ingredient()

    # 1. Start fermentation
    resp = admin_client.post(
        "/api/brew/fermentations",
        json={
            "container_id": 1,
            "start_date": "2025-01-01",
            "stage": "primary",
        },
    )
    assert resp.status_code == 200

    # 2. Add ingredient
    resp = admin_client.post(
        "/api/brew/additions",
        json={
            "container_id": 1,
            "ingredient_name": "Grape Juice",
            "date": "2025-01-01",
            "starting_amount": 0,
            "ending_amount": 3000,
            "unit": "mL",
        },
    )
    assert resp.status_code == 200

    # 3. SG measurement
    resp = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-01",
            "specific_gravity": 1.090,
        },
    )
    assert resp.status_code == 200

    # 4. Rack to secondary
    resp = admin_client.post(
        "/api/brew/rack",
        json={
            "from_container_id": 1,
            "to_container_id": 2,
            "date": "2025-02-01",
            "stage": "secondary",
        },
    )
    assert resp.status_code == 200

    # 5. Another SG measurement on secondary
    resp = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 2,
            "measurement_date": "2025-02-15",
            "specific_gravity": 0.998,
        },
    )
    assert resp.status_code == 200

    # 6. Bottle from secondary
    resp = admin_client.post(
        "/api/brew/bottle",
        json={
            "from_container_id": 2,
            "to_container_id": 3,
            "date": "2025-03-01",
            "amount": 750,
            "unit": "mL",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["fermentation_id"] == 1  # same fermentation through the chain


# --- Validation ---


def test_bottle_invalid_unit(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/bottle",
        json={
            "from_container_id": 1,
            "to_container_id": 3,
            "date": "2025-03-01",
            "amount": 750.0,
            "unit": "gallons",
        },
    )
    assert resp.status_code == 422


def test_rack_same_container(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.post(
        "/api/brew/rack",
        json={
            "from_container_id": 1,
            "to_container_id": 1,
            "date": "2025-02-01",
        },
    )
    assert resp.status_code == 400


def test_explicit_datetime_ordering(admin_client):
    """Two SG measurements on the same calendar day with explicit datetimes
    should both land in the active fermentation without ordering collisions."""
    _seed_container_with_fermentation()
    resp1 = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "measurement_datetime": "2025-01-15T09:00:00",
            "specific_gravity": 1.090,
        },
    )
    resp2 = admin_client.post(
        "/api/brew/sg-measurements",
        json={
            "container_id": 1,
            "measurement_date": "2025-01-15",
            "measurement_datetime": "2025-01-15T17:00:00",
            "specific_gravity": 1.050,
        },
    )
    assert resp1.status_code == 200
    assert resp2.status_code == 200


# --- End fermentation ---


def test_end_fermentation(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.patch(
        "/api/brew/fermentations/1",
        json={"end_date": "2025-06-01", "end_mass": 4900.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["end_date"] is not None
    assert data["end_mass"] == 4900.0

    db = TestSession()
    log = db.query(ContainerFermentationLog).filter_by(container_id=1).first()
    assert log.end_date is not None
    db.close()


def test_end_fermentation_not_found(admin_client):
    resp = admin_client.patch("/api/brew/fermentations/999", json={})
    assert resp.status_code == 404


# --- Active fermentations ---


def test_active_fermentations_empty(admin_client):
    resp = admin_client.get("/api/brew/fermentations/active")
    assert resp.status_code == 200
    assert resp.json() == []


def test_active_fermentations_lists_open(admin_client):
    _seed_container_with_fermentation()
    resp = admin_client.get("/api/brew/fermentations/active")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["fermentation_id"] == 1
    assert data[0]["container_id"] == 1


def test_active_fermentations_excludes_ended(admin_client):
    _seed_container_with_fermentation()
    admin_client.patch("/api/brew/fermentations/1", json={"end_date": "2025-06-01"})
    resp = admin_client.get("/api/brew/fermentations/active")
    assert resp.json() == []


# --- Open-log uniqueness (race guard) ---


def test_open_log_uniqueness_enforced(admin_client, db):
    """The partial unique index must prevent two open logs on the same container."""
    from sqlalchemy.exc import IntegrityError

    _seed_container_with_fermentation()
    db.add(Fermentation(id=2, start_date=date(2025, 2, 1)))
    db.flush()
    db.add(
        ContainerFermentationLog(
            container_id=1,
            fermentation_id=2,
            start_date=datetime(2025, 2, 1),
        )
    )
    try:
        db.commit()
        committed = True
    except IntegrityError:
        db.rollback()
        committed = False
    assert committed is False
