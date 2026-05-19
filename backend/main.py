"""
Ground Control Station — FastAPI application entry point.
=========================================================

Provides REST API endpoints and a WebSocket telemetry feed for the
Robot Management System dashboard.  Integrates JWT authentication,
Role-Based Access Control (RBAC), and persistent mission logging.
"""

import asyncio
import json
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import router as auth_router, require_viewer, require_commander, get_current_user
from database import init_db, get_db, MissionLog, CommandType, User
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


# ── Audit-log helper ──────────────────────────────────────────────────────

def _log_command(
    db: Session,
    command_type: CommandType,
    user: User | None = None,
    payload: dict | None = None,
    robot_status: str = "unknown",
    response: dict | None = None,
) -> MissionLog:
    """Persist a command to the mission audit log.

    Every command sent to the robot is recorded with the acting user,
    timestamp (auto-set by the model), request payload, and response.
    This satisfies the safety-auditing requirement in the brief.
    """
    entry = MissionLog(
        user_id=user.id if user else None,
        command_type=command_type,
        payload=json.dumps(payload or {}),
        robot_status=robot_status,
        response=json.dumps(response or {}),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ── Application factory ──────────────────────────────────────────────────
app = FastAPI(
    title="Ground Control Station",
    description="CMP9134 — Robot Management System with Authentication and Audit Logging",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-routers
app.include_router(auth_router)
app.include_router(legacy_stats_router)


# ── Startup event — create DB tables ─────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """Initialise the database tables on application boot."""
    init_db()
    logger.info("Database tables created / verified")


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ── Robot status (VIEWER or COMMANDER) ────────────────────────────────────
@app.get("/api/status")
async def get_status(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Return the current robot status (position, battery level, state).

    Requires authentication (any role).
    Logs the status request to the mission audit trail.
    """
    try:
        result = await robot.get_status()
        _log_command(db, CommandType.STATUS, current_user, response=result,
                     robot_status=result.get("status", "unknown"))
        return result
    except RobotConnectionError as exc:
        logger.warning("Could not reach robot API: %s", exc)
        _log_command(db, CommandType.STATUS, current_user,
                     response={"error": str(exc)}, robot_status="unreachable")
        return {"error": str(exc)}


# ── Move robot (COMMANDER only) ──────────────────────────────────────────
@app.post("/api/move")
async def move_robot(
    request: MoveRequest,
    current_user: User = Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Send the robot to position (x, y) on the 21x21 grid.

    Requires COMMANDER role — viewers receive 403 Forbidden.
    The command and response are logged for safety auditing.
    """
    payload = {"x": request.x, "y": request.y}
    try:
        result = await robot.move(request.x, request.y)
        logger.info("Move command sent by %s: (%d, %d)",
                     current_user.username, request.x, request.y)
        _log_command(db, CommandType.MOVE, current_user, payload=payload,
                     response=result, robot_status=result.get("status", "unknown"))
        return result
    except RobotConnectionError as exc:
        logger.warning("Move command failed: %s", exc)
        _log_command(db, CommandType.MOVE, current_user, payload=payload,
                     response={"error": str(exc)}, robot_status="unreachable")
        return {"error": str(exc)}


# ── Reset robot (COMMANDER only) ─────────────────────────────────────────
@app.post("/api/reset")
async def reset_robot(
    current_user: User = Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Reset the robot simulation to its initial state.

    Requires COMMANDER role. Logged for auditing.
    """
    try:
        result = await robot.reset()
        logger.info("Robot reset by %s", current_user.username)
        _log_command(db, CommandType.RESET, current_user, response=result)
        return result
    except RobotConnectionError as exc:
        logger.warning("Reset command failed: %s", exc)
        _log_command(db, CommandType.RESET, current_user,
                     response={"error": str(exc)}, robot_status="unreachable")
        return {"error": str(exc)}


# ── Map data (any authenticated user) ────────────────────────────────────
@app.get("/api/map")
async def get_map(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Fetch the current 21x21 map grid with obstacles and robot position."""
    try:
        result = await robot.get_map()
        _log_command(db, CommandType.MAP, current_user, response={"grid": "ok"})
        return result
    except RobotConnectionError as exc:
        logger.warning("Map request failed: %s", exc)
        return {"error": str(exc)}


# ── Sensor data (any authenticated user) ─────────────────────────────────
@app.get("/api/sensors")
async def get_sensors(
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Fetch current sensor readings from the robot."""
    try:
        result = await robot.get_sensors()
        _log_command(db, CommandType.SENSOR, current_user, response={"sensors": "ok"})
        return result
    except RobotConnectionError as exc:
        logger.warning("Sensor request failed: %s", exc)
        return {"error": str(exc)}


# ── Mission audit log endpoint ───────────────────────────────────────────
@app.get("/api/logs")
def get_logs(
    limit: int = Query(50, ge=1, le=500, description="Number of log entries"),
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieve the most recent mission audit log entries.

    Returns a list of logged commands with timestamps, users, and outcomes.
    Newest entries first.
    """
    logs = (
        db.query(MissionLog)
        .order_by(MissionLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user": log.user.username if log.user else "system",
            "command_type": log.command_type.value,
            "payload": log.payload,
            "robot_status": log.robot_status,
            "response": log.response,
        }
        for log in logs
    ]


# ── WebSocket telemetry feed ──────────────────────────────────────────────
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """Stream live robot telemetry data to connected browser clients.

    WebSockets maintain a persistent two-way connection, ideal for
    low-latency telemetry feeds.  The server pushes status updates
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
                await websocket.send_json({
                    "error": str(exc),
                    "status": "disconnected",
                })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("Telemetry WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
