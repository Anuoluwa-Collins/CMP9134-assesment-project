"""Shared test fixtures for the GCS backend test suite."""

import sys
import os

# Add backend directory to path so tests can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use SQLite for tests (not PostgreSQL)
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from database import Base, engine, SessionLocal, User, UserRole
from auth import hash_password, create_access_token


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create fresh database tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a DB session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_commander(db_session):
    """Create a commander user and return (user, token)."""
    user = User(
        username="cmd_user",
        hashed_password=hash_password("testpass123"),
        role=UserRole.COMMANDER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return user, token


@pytest.fixture
def test_viewer(db_session):
    """Create a viewer user and return (user, token)."""
    user = User(
        username="view_user",
        hashed_password=hash_password("testpass123"),
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return user, token


@pytest.fixture
def mock_robot_status():
    """Sample robot status response for testing."""
    return {
        "id": "robot-001",
        "status": "idle",
        "position": {"x": 10, "y": 10},
        "battery": 85.5,
    }


@pytest.fixture
def mock_map_data():
    """Sample map response for testing."""
    return {
        "grid_size": 21,
        "robot": {"x": 10, "y": 10},
        "obstacles": [{"x": 5, "y": 5}, {"x": 15, "y": 12}],
    }


@pytest.fixture
def mock_sensor_data():
    """Sample sensor response for testing."""
    return {
        "proximity": {"north": 3.2, "south": 8.1, "east": 5.0, "west": 12.4},
        "temperature": 22.5,
        "battery": 85.5,
    }
