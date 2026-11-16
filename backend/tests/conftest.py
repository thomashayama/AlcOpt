import os

# The app's startup hook runs init_db() on the engine built from DATABASE_URL.
# Point it at an in-memory database before alcopt is imported, so the tests
# never open (or need) data/alcopt.db or whatever DATABASE_URL is set to.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from alcopt.api.dependencies import (  # noqa: E402
    get_db,
    get_current_user,
    get_optional_user,
    require_admin,
)
from alcopt.api.main import app  # noqa: E402
from alcopt.database.models import Base  # noqa: E402


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


ADMIN_USER = {"email": "admin@test.com", "picture": ""}
REGULAR_USER = {"email": "user@test.com", "picture": ""}


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Provide a test DB session."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """Unauthenticated test client."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_admin, None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def user_client():
    """Test client authenticated as a regular user."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: REGULAR_USER
    app.dependency_overrides[get_optional_user] = lambda: REGULAR_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client():
    """Test client authenticated as an admin user."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    app.dependency_overrides[require_admin] = lambda: ADMIN_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
