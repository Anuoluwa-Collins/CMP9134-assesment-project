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
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client


def auth_header(token):
    """Helper to build auth header dict."""
    return {"Authorization": f"Bearer {token}"}


# ── Health check ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Health endpoint should always return 200 with status ok (no auth)."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── GET /api/status (requires VIEWER+) ────────────────────────────────────

@pytest.mark.asyncio
async def test_status_requires_auth(async_client):
    """Status endpoint returns 401 without a token."""
    response = await async_client.get("/api/status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_status_success_with_commander(
        async_client, test_commander, mock_robot_status):
    """Status endpoint returns robot data for authenticated commander."""
    _, token = test_commander
    with patch("main.robot.get_status", new_callable=AsyncMock) as mock:
        mock.return_value = mock_robot_status
        response = await async_client.get(
            "/api/status", headers=auth_header(token)
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "robot-001"
    assert data["battery"] == 85.5


@pytest.mark.asyncio
async def test_status_success_with_viewer(
        async_client, test_viewer, mock_robot_status):
    """Status endpoint is accessible to viewers."""
    _, token = test_viewer
    with patch("main.robot.get_status", new_callable=AsyncMock) as mock:
        mock.return_value = mock_robot_status
        response = await async_client.get(
            "/api/status", headers=auth_header(token)
        )

    assert response.status_code == 200
    assert response.json()["id"] == "robot-001"


@pytest.mark.asyncio
async def test_status_robot_unreachable(async_client, test_viewer):
    """Status endpoint returns error when robot API is down."""
    _, token = test_viewer
    with patch("main.robot.get_status", new_callable=AsyncMock) as mock:
        mock.side_effect = RobotConnectionError("Robot unreachable")
        response = await async_client.get(
            "/api/status", headers=auth_header(token)
        )

    assert response.status_code == 200
    assert "error" in response.json()


# ── POST /api/move (requires COMMANDER) ───────────────────────────────────

@pytest.mark.asyncio
async def test_move_requires_auth(async_client):
    """Move endpoint returns 401 without a token."""
    response = await async_client.post("/api/move", json={"x": 5, "y": 3})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_move_forbidden_for_viewer(async_client, test_viewer):
    """Move endpoint returns 403 for viewer role."""
    _, token = test_viewer
    response = await async_client.post(
        "/api/move", json={"x": 5, "y": 3}, headers=auth_header(token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_move_success_for_commander(async_client, test_commander):
    """Move endpoint sends coordinates for commander role."""
    _, token = test_commander
    move_result = {"status": "ok", "position": {"x": 5, "y": 3}}
    with patch("main.robot.move", new_callable=AsyncMock) as mock:
        mock.return_value = move_result
        response = await async_client.post(
            "/api/move", json={"x": 5, "y": 3}, headers=auth_header(token)
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    mock.assert_called_once_with(5, 3)


@pytest.mark.asyncio
async def test_move_invalid_coords(async_client, test_commander):
    """Move endpoint rejects coordinates outside 0-20 range."""
    _, token = test_commander
    response = await async_client.post(
        "/api/move", json={"x": 25, "y": 0}, headers=auth_header(token)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_move_missing_fields(async_client, test_commander):
    """Move endpoint rejects requests with missing fields."""
    _, token = test_commander
    response = await async_client.post(
        "/api/move", json={"x": 5}, headers=auth_header(token)
    )
    assert response.status_code == 422


# ── POST /api/reset (requires COMMANDER) ──────────────────────────────────

@pytest.mark.asyncio
async def test_reset_forbidden_for_viewer(async_client, test_viewer):
    """Reset endpoint returns 403 for viewer role."""
    _, token = test_viewer
    response = await async_client.post(
            "/api/reset", headers=auth_header(token)
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reset_success_for_commander(async_client, test_commander):
    """Reset endpoint returns confirmation for commander."""
    _, token = test_commander
    with patch("main.robot.reset", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "ok", "message": "Robot reset"}
        response = await async_client.post(
            "/api/reset", headers=auth_header(token)
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── GET /api/map ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_map_success(async_client, test_viewer, mock_map_data):
    """Map endpoint returns grid data for authenticated user."""
    _, token = test_viewer
    with patch("main.robot.get_map", new_callable=AsyncMock) as mock:
        mock.return_value = mock_map_data
        response = await async_client.get(
            "/api/map", headers=auth_header(token)
        )

    assert response.status_code == 200
    assert response.json()["grid_size"] == 21


# ── GET /api/sensors ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sensors_success(async_client, test_viewer, mock_sensor_data):
    """Sensors endpoint returns readings for authenticated user."""
    _, token = test_viewer
    with patch("main.robot.get_sensors", new_callable=AsyncMock) as mock:
        mock.return_value = mock_sensor_data
        response = await async_client.get(
            "/api/sensors",
            headers=auth_header(token)
        )

    assert response.status_code == 200
    assert response.json()["temperature"] == 22.5


# ── GET /api/logs ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logs_requires_auth(async_client):
    """Logs endpoint returns 401 without a token."""
    response = await async_client.get("/api/logs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logs_returns_empty_list(async_client, test_viewer):
    """Logs endpoint returns empty list when no commands logged yet."""
    _, token = test_viewer
    response = await async_client.get("/api/logs", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json() == []
