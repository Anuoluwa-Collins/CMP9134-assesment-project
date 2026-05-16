"""
Ground Control Station — FastAPI application entry point.
=========================================================

Provides REST API endpoints and a WebSocket telemetry feed for the
Robot Management System dashboard. Proxies requests to the Virtual
Robot API via the RobotClient.
"""

import asyncio
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from legacy_stats import router as legacy_stats_router
from robot_client import robot, RobotConnectionError

# ── Configuration ─────────────────────────────────────────────────────────
ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


# ── Request/Response models ───────────────────────────────────────────────
class MoveRequest(BaseModel):
    """Validated request body for the move endpoint."""
    x: int = Field(..., ge=0, le=20, description="Target X coordinate (0-20)")
    y: int = Field(..., ge=0, le=20, description="Target Y coordinate (0-20)")


# ── Application factory ──────────────────────────────────────────────────
app = FastAPI(
    title="Ground Control Station",
    description="CMP9134 — Robot Management System",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach legacy stats router (for refactoring exercise)
app.include_router(legacy_stats_router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ── Robot status ──────────────────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    """Return the current robot status (position, battery level, state).

    Proxies the request to the Virtual Robot API via RobotClient.
    Includes retry logic for handling chaos monkey 503 errors.
    """
    try:
        return await robot.get_status()
    except RobotConnectionError as exc:
        logger.warning("Could not reach robot API: %s", exc)
        return {"error": str(exc)}


# ── Move robot ────────────────────────────────────────────────────────────
@app.post("/api/move")
async def move_robot(request: MoveRequest):
    """Send the robot to position (x, y) on the 21x21 grid.

    The request body must contain x and y integers between 0 and 20.
    FastAPI automatically validates these constraints via the Pydantic model.
    Returns the robot API response or an error message if unreachable.
    """
    try:
        result = await robot.move(request.x, request.y)
        logger.info("Move command sent: (%d, %d)", request.x, request.y)
        return result
    except RobotConnectionError as exc:
        logger.warning("Move command failed: %s", exc)
        return {"error": str(exc)}


# ── Reset robot ───────────────────────────────────────────────────────────
@app.post("/api/reset")
async def reset_robot():
    """Reset the robot simulation to its initial state.

    Clears the robot's position, battery, and sensor state back to defaults.
    """
    try:
        result = await robot.reset()
        logger.info("Robot reset successfully")
        return result
    except RobotConnectionError as exc:
        logger.warning("Reset command failed: %s", exc)
        return {"error": str(exc)}


# ── Map data ──────────────────────────────────────────────────────────────
@app.get("/api/map")
async def get_map():
    """Fetch the current 21x21 map grid with obstacles and robot position.

    Returns the full map state from the robot simulator, including
    obstacle locations and the robot's current cell.
    """
    try:
        return await robot.get_map()
    except RobotConnectionError as exc:
        logger.warning("Map request failed: %s", exc)
        return {"error": str(exc)}


# ── Sensor data ───────────────────────────────────────────────────────────
@app.get("/api/sensors")
async def get_sensors():
    """Fetch current sensor readings from the robot.

    Returns proximity, temperature, and other sensor data.
    Note: readings may include simulated noise from the robot simulator.
    """
    try:
        return await robot.get_sensors()
    except RobotConnectionError as exc:
        logger.warning("Sensor request failed: %s", exc)
        return {"error": str(exc)}


# ── WebSocket telemetry feed ──────────────────────────────────────────────
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """Stream live robot telemetry data to connected browser clients.

    WebSockets maintain a persistent two-way connection, ideal for
    low-latency telemetry feeds. The server pushes status updates
    every 500ms without the client needing to poll.

    If the robot API is unreachable, an error payload is sent instead
    of disconnecting, so the client can display a warning and recover
    when the connection is restored.
    """
    await websocket.accept()
    logger.info("Telemetry WebSocket client connected")
    try:
        while True:
            try:
                data = await robot.get_status()
                await websocket.send_json(data)
            except RobotConnectionError as exc:
                # Send error payload instead of disconnecting
                await websocket.send_json({
                    "error": str(exc),
                    "status": "disconnected",
                })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("Telemetry WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
