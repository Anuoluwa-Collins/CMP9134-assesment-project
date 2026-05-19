"""
Robot API client — async wrapper around the Virtual Robot REST API.

Features:
- All robot endpoints: status, move, reset, map, sensors
- Automatic retry with exponential backoff for chaos monkey (503s)
- Structured logging for debugging and audit trail
- Configurable via environment variables
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")
MAX_RETRIES = int(os.getenv("ROBOT_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("ROBOT_RETRY_BACKOFF", "0.5"))
REQUEST_TIMEOUT = float(os.getenv("ROBOT_TIMEOUT", "5.0"))

logger = logging.getLogger(__name__)


class RobotConnectionError(Exception):
    """Raised when a request to the robot API fails after all retries."""


def _backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay for a given attempt number."""
    return RETRY_BACKOFF * (2 ** (attempt - 1))


async def _send_request(
    client: httpx.AsyncClient, method: str, url: str,
    json_body: dict | None, timeout: float,
) -> httpx.Response:
    """Send a single HTTP request using the given method."""
    if method.upper() == "POST":
        return await client.post(url, json=json_body, timeout=timeout)
    return await client.get(url, timeout=timeout)


class RobotClient:
    """Async HTTP client for the Virtual Robot API.

    Includes built-in retry logic.
    """

    def __init__(self, base_url: str = ROBOT_API_URL) -> None:
        self._base = base_url.rstrip("/")

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
    ) -> dict[str, Any]:
        """Send an HTTP request with automatic retry on transient failures.

        Implements exponential backoff: wait 0.5s, 1s, 2s, etc.
        Retries on 503 (Service Unavailable) which the chaos monkey produces,
        as well as network timeouts and connection errors.
        """
        url = f"{self._base}{path}"
        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = await self._single_attempt(
                    method, url, json_body, path, attempt
                )
                if result is not None:
                    return result
                last_exc = RobotConnectionError(
                    f"Robot API returned 503 on attempt {attempt}"
                )
            except RobotConnectionError:
                raise
            except Exception as exc:
                logger.warning(
                    "Request to %s %s failed (attempt %d/%d): %s",
                    method, path, attempt, MAX_RETRIES, exc,
                )
                last_exc = exc

            if attempt < MAX_RETRIES:
                await asyncio.sleep(_backoff_delay(attempt))

        raise RobotConnectionError(
            f"Robot unreachable after {MAX_RETRIES} attempts: {last_exc}"
        ) from last_exc

    async def _single_attempt(
        self, method: str, url: str, json_body: dict | None,
        path: str, attempt: int,
    ) -> dict[str, Any] | None:
        """Execute one request attempt. Returns None on 503 (retry signal)."""
        async with httpx.AsyncClient() as client:
            response = await _send_request(
                client, method, url, json_body, REQUEST_TIMEOUT
            )

            if response.status_code == 503:
                logger.warning(
                    "Robot API returned 503 on %s %s (attempt %d/%d)",
                    method, path, attempt, MAX_RETRIES,
                )
                return None

            response.raise_for_status()
            return response.json()

    # ── Core endpoints ────────────────────────────────────────────────────

    async def get_status(self) -> dict[str, Any]:
        """Fetch current robot status (position, battery, state)."""
        return await self._request_with_retry("GET", "/api/status")

    async def move(self, x: int, y: int) -> dict[str, Any]:
        """Send a move command.


        Args:
            x: Target x coordinate (0-20 on the 21x21 grid).
            y: Target y coordinate (0-20 on the 21x21 grid).

        Returns:
            JSON response from the robot API confirming the move.

        Raises:
            RobotConnectionError: If the robot API is
                unreachable after retries.
        """
        return await self._request_with_retry(
            "POST", "/api/move", {"x": x, "y": y}
        )

    async def reset(self) -> dict[str, Any]:
        """Reset the robot simulation to its initial state.

        Returns:
            JSON response confirming the reset.

        Raises:
            RobotConnectionError: If the robot API is unreachable.
        """
        return await self._request_with_retry("POST", "/api/reset")

    async def get_map(self) -> dict[str, Any]:
        """Fetch the current map state including obstacles and robot position.

        Returns:
            JSON with map grid data, obstacle positions, and robot location.
        """
        return await self._request_with_retry("GET", "/api/map")

    async def get_sensors(self) -> dict[str, Any]:
        """Fetch current sensor readings (proximity, temperature, etc.).

        Returns:
            JSON with sensor data. Note: readings may include simulated noise.
        """
        return await self._request_with_retry("GET", "/api/sensors")


# Module-level singleton used by main.py
robot = RobotClient()
