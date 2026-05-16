"""Tests for the legacy_stats module (before and after refactoring).

These tests pin the current behaviour so refactoring in Week 12
can be verified — changes must not break existing functionality.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from legacy_stats import _compute_base_score, _cap_score


# ── Unit tests for helper functions ──────────────────────────────────────

class TestComputeBaseScore:
    """Tests for the _compute_base_score function."""

    def test_positive_inputs(self):
        """Score is (distance * multiplier) / battery."""
        assert _compute_base_score(100.0, 50.0, 2.0) == 4.0

    def test_zero_distance_returns_zero(self):
        """Zero distance means no score."""
        assert _compute_base_score(0, 50.0, 2.0) == 0

    def test_negative_distance_returns_zero(self):
        """Negative distance is invalid — returns zero."""
        assert _compute_base_score(-10, 50.0, 2.0) == 0

    def test_zero_battery_returns_zero(self):
        """Zero battery is invalid — returns zero (avoids division by zero)."""
        assert _compute_base_score(100.0, 0, 2.0) == 0

    def test_negative_battery_returns_zero(self):
        """Negative battery returns zero."""
        assert _compute_base_score(100.0, -5, 2.0) == 0


class TestCapScore:
    """Tests for the _cap_score function."""

    def test_below_max(self):
        assert _cap_score(50.0) == 50.0

    def test_at_max(self):
        assert _cap_score(100.0) == 100.0

    def test_above_max(self):
        assert _cap_score(150.0) == 100.0


# ── Integration tests via the API endpoint ───────────────────────────────

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_recon_mission(async_client):
    """Type 1 (recon) mission with valid data returns success."""
    response = await async_client.post("/api/mission_stats", json={
        "type": 1, "dist": 100, "batt": 50
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mission"] == "recon"
    assert data["final_score"] == 20.0


@pytest.mark.asyncio
async def test_transport_mission_with_heavy_payload(async_client):
    """Transport mission with payload > 50 applies penalty."""
    response = await async_client.post("/api/mission_stats", json={
        "type": 2, "dist": 100, "batt": 50, "payload_weight": 60
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mission"] == "transport"
    assert data["final_score"] == 4.0


@pytest.mark.asyncio
async def test_invalid_mission_type(async_client):
    """Unknown mission type returns error status."""
    response = await async_client.post("/api/mission_stats", json={
        "type": 99, "dist": 100, "batt": 50
    })
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_missing_required_fields(async_client):
    """Missing fields return 400."""
    response = await async_client.post("/api/mission_stats", json={
        "type": 1
    })
    assert response.status_code == 400
