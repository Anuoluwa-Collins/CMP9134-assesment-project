"""Integration tests for the FastAPI endpoints in main.py."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from main import app
from robot_client import RobotConnectionError


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ── Health check ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Health endpoint should always return 200 with status ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── GET /api/status ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_status_endpoint_success(async_client, mock_robot_status):
    """Status endpoint returns robot data when API is reachable."""
    with patch("main.robot.get_status", new_callable=AsyncMock) as mock:
        mock.return_value = mock_robot_status
        response = await async_client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "robot-001"
    assert data["battery"] == 85.5


@pytest.mark.asyncio
async def test_status_endpoint_robot_unreachable(async_client):
    """Status endpoint returns error dict when robot API is down."""
    with patch("main.robot.get_status", new_callable=AsyncMock) as mock:
        mock.side_effect = RobotConnectionError("Robot unreachable")
        response = await async_client.get("/api/status")

    assert response.status_code == 200
    assert "error" in response.json()


# ── POST /api/move ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_endpoint_success(async_client):
    """Move endpoint sends coordinates and returns confirmation."""
    move_result = {"status": "ok", "position": {"x": 5, "y": 3}}
    with patch("main.robot.move", new_callable=AsyncMock) as mock:
        mock.return_value = move_result
        response = await async_client.post("/api/move", json={"x": 5, "y": 3})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    mock.assert_called_once_with(5, 3)


@pytest.mark.asyncio
async def test_move_endpoint_invalid_coords(async_client):
    """Move endpoint rejects coordinates outside 0-20 range."""
    response = await async_client.post("/api/move", json={"x": 25, "y": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_move_endpoint_missing_fields(async_client):
    """Move endpoint rejects requests with missing fields."""
    response = await async_client.post("/api/move", json={"x": 5})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_move_endpoint_robot_unreachable(async_client):
    """Move endpoint returns error when robot API is down."""
    with patch("main.robot.move", new_callable=AsyncMock) as mock:
        mock.side_effect = RobotConnectionError("503 chaos monkey")
        response = await async_client.post("/api/move", json={"x": 5, "y": 3})

    assert response.status_code == 200
    assert "error" in response.json()


# ── POST /api/reset ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reset_endpoint_success(async_client):
    """Reset endpoint returns confirmation on success."""
    reset_result = {"status": "ok", "message": "Robot reset"}
    with patch("main.robot.reset", new_callable=AsyncMock) as mock:
        mock.return_value = reset_result
        response = await async_client.post("/api/reset")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_reset_endpoint_robot_unreachable(async_client):
    """Reset endpoint returns error when robot API is down."""
    with patch("main.robot.reset", new_callable=AsyncMock) as mock:
        mock.side_effect = RobotConnectionError("Robot unreachable")
        response = await async_client.post("/api/reset")

    assert response.status_code == 200
    assert "error" in response.json()


# ── GET /api/map ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_map_endpoint_success(async_client, mock_map_data):
    """Map endpoint returns grid data on success."""
    with patch("main.robot.get_map", new_callable=AsyncMock) as mock:
        mock.return_value = mock_map_data
        response = await async_client.get("/api/map")

    assert response.status_code == 200
    data = response.json()
    assert data["grid_size"] == 21


# ── GET /api/sensors ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sensors_endpoint_success(async_client, mock_sensor_data):
    """Sensors endpoint returns sensor readings on success."""
    with patch("main.robot.get_sensors", new_callable=AsyncMock) as mock:
        mock.return_value = mock_sensor_data
        response = await async_client.get("/api/sensors")

    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == 22.5


@pytest.mark.asyncio
async def test_sensors_endpoint_robot_unreachable(async_client):
    """Sensors endpoint returns error when robot API is down."""
    with patch("main.robot.get_sensors", new_callable=AsyncMock) as mock:
        mock.side_effect = RobotConnectionError("Robot unreachable")
        response = await async_client.get("/api/sensors")

    assert response.status_code == 200
    assert "error" in response.json()
