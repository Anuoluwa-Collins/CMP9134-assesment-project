"""Shared test fixtures for the GCS backend test suite."""

import sys
import os

# Add backend directory to path so tests can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


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
