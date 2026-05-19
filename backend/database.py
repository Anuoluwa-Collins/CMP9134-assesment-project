"""
Database configuration and ORM models.
======================================

Uses SQLAlchemy (async) with SQLite for local development and
PostgreSQL in production. Models cover user accounts and the
mission audit-log required by the assessment brief.
"""

from __future__ import annotations

import os
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum as SAEnum,
    ForeignKey, Text, create_engine,
)
from sqlalchemy.orm import (
    declarative_base, sessionmaker, relationship,
)

# ── Configuration ─────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./gcs.db",          # default: local SQLite file
)

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── Enums ─────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """Role-Based Access Control roles."""
    VIEWER = "viewer"          # read-only: telemetry + map
    COMMANDER = "commander"    # can also send move/reset commands


class CommandType(str, enum.Enum):
    """Types of commands that can be logged."""
    MOVE = "move"
    RESET = "reset"
    STATUS = "status"
    MAP = "map"
    SENSOR = "sensor"
    LOGIN = "login"
    REGISTER = "register"


# ── Models ────────────────────────────────────────────────────────────────

class User(Base):
    """User account with role-based access control.

    Attributes:
        id:              Auto-incrementing primary key.
        username:        Unique login name.
        hashed_password: bcrypt hash — never store plaintext.
        role:            VIEWER (read-only) or COMMANDER (full control).
        created_at:      Account creation timestamp (UTC).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    # Relationship to audit logs
    logs = relationship("MissionLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"


class MissionLog(Base):
    """Persistent audit trail for every command sent to the robot.

    Records timestamp, acting user, command type, payload, and the
    robot's response — satisfying the safety-auditing requirement.

    Attributes:
        id:           Auto-incrementing primary key.
        timestamp:    When the command was issued (UTC).
        user_id:      FK to the user who issued the command.
        command_type: Category of the command (move, reset, etc.).
        payload:      JSON-serialised request body (e.g. {"x":5,"y":3}).
        robot_status: Robot state at time of command (IDLE, MOVING, etc.).
        response:     JSON-serialised API response or error message.
    """
    __tablename__ = "mission_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    command_type = Column(SAEnum(CommandType), nullable=False)
    payload = Column(Text, default="{}")
    robot_status = Column(String(50), default="unknown")
    response = Column(Text, default="{}")

    user = relationship("User", back_populates="logs")

    def __repr__(self) -> str:
        return (
            f"<MissionLog {self.command_type.value}"
            f" by user_id={self.user_id}>"
        )


# ── Database initialisation ──────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session, closes on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
