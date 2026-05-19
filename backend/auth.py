"""
Authentication & authorisation module.
======================================

Implements JWT-based authentication with Role-Based Access Control
(RBAC) differentiating VIEWER (read-only) and COMMANDER (full
control) roles, as required by the assessment brief.

Features:
- User registration with bcrypt password hashing
- Login returning a signed JWT access token
- Dependency-injection helpers for protecting routes
- Role-based guards (require_viewer, require_commander)
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db, User, UserRole

# ── Configuration ─────────────────────────────────────────────────────────
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "change-me-in-production-use-a-real-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Pydantic schemas ──────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole = Field(default=UserRole.VIEWER)


class RegisterResponse(BaseModel):
    """Response after successful registration."""
    id: int
    username: str
    role: str
    message: str


class TokenResponse(BaseModel):
    """JWT token returned on successful login."""
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserInfo(BaseModel):
    """Public user information (no password)."""
    id: int
    username: str
    role: str


# ── Password helpers ──────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────

def create_access_token(
        data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload claims (must include 'sub' for username).
        expires_delta: Custom expiry; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependency: get current user from JWT ─────────────────────────────────

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT Bearer token.

    Raises HTTPException 401 if the token is invalid or the user
    no longer exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ── Role-based guards ─────────────────────────────────────────────────────

async def require_viewer(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Allow any authenticated user (VIEWER or COMMANDER)."""
    return current_user


async def require_commander(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Only allow COMMANDER role — reject VIEWER with 403."""
    if current_user.role != UserRole.COMMANDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Commander role required for this action",
        )
    return current_user


# ── Routes ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account.

    Hashes the password with bcrypt before storing. Returns 409
    if the username is already taken.
    """
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User registered: %s (%s)", user.username, user.role.value)
    return RegisterResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        message="Registration successful",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate user and return a JWT access token.

    Uses OAuth2 password flow (username + password in form body).
    Returns 401 if credentials are invalid.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(
            form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    logger.info("User logged in: %s", user.username)
    return TokenResponse(
        access_token=token,
        role=user.role.value,
        username=user.username,
    )


@router.get("/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
    )
