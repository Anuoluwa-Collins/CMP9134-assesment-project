"""Unit tests for robot_client.py — RobotClient with retry logic."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from robot_client import RobotClient, RobotConnectionError


@pytest.fixture
def client():
    """Create a RobotClient pointing at a fake URL."""
    return RobotClient(base_url="http://fake-robot:5000")


# ── get_status tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_status_success(client, mock_robot_status):
    """Test that get_status returns parsed JSON on a 200 response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_robot_status
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        result = await client.get_status()

    assert result["id"] == "robot-001"
    assert result["position"]["x"] == 10
    assert result["battery"] == 85.5


@pytest.mark.asyncio
async def test_get_status_connection_error(client):
    """Test that get_status raises RobotConnectionError on network failure."""
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        with patch("robot_client.MAX_RETRIES", 1):
            with pytest.raises(RobotConnectionError):
                await client.get_status()


# ── move tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_success(client):
    """Test that move sends a POST with correct JSON body."""
    move_response = {"status": "ok", "position": {"x": 5, "y": 3}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = move_response
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        result = await client.move(5, 3)

    assert result["status"] == "ok"
    assert result["position"]["x"] == 5
    mock_http_client.post.assert_called_once()
    call_kwargs = mock_http_client.post.call_args
    assert call_kwargs.kwargs.get("json") == {"x": 5, "y": 3}


# ── reset tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reset_success(client):
    """Test that reset sends a POST and returns confirmation."""
    reset_response = {"status": "ok", "message": "Robot reset"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = reset_response
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        result = await client.reset()

    assert result["status"] == "ok"


# ── retry logic tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_on_503(client):
    """Test that 503 triggers a retry and eventually succeeds."""
    fail_response = MagicMock()
    fail_response.status_code = 503

    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.json.return_value = {"status": "ok"}
    ok_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=[fail_response, ok_response])
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        with patch("robot_client.RETRY_BACKOFF", 0.01):
            result = await client.get_status()

    assert result["status"] == "ok"
    assert mock_http_client.get.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises_error(client):
    """Test that exhausting all retries raises RobotConnectionError."""
    fail_response = MagicMock()
    fail_response.status_code = 503

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=fail_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        with patch("robot_client.MAX_RETRIES", 2):
            with patch("robot_client.RETRY_BACKOFF", 0.01):
                with pytest.raises(RobotConnectionError, match="after 2 attempts"):
                    await client.get_status()


# ── get_map tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_map_success(client, mock_map_data):
    """Test that get_map returns parsed map JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_map_data
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        result = await client.get_map()

    assert result["grid_size"] == 21
    assert len(result["obstacles"]) == 2


# ── get_sensors tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sensors_success(client, mock_sensor_data):
    """Test that get_sensors returns parsed sensor JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_sensor_data
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("robot_client.httpx.AsyncClient", return_value=mock_http_client):
        result = await client.get_sensors()

    assert result["temperature"] == 22.5
    assert "proximity" in result
