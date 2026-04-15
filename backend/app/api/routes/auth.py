"""Simple token-based auth for multiplayer sessions."""
import hashlib
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import storage
from app.db import get_db
import app.repository as repo

router = APIRouter(prefix="/auth")

security = HTTPBearer(auto_error=False)


# ── Schemas ──


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=3)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str


class LoginResponse(BaseModel):
    token: str
    username: str
    id: str


# ── Password hashing (simple HMAC — not bcrypt, fine for in-memory) ──


_SALT = "dungeon-master-salt"


def _hash_password(password: str) -> str:
    return hashlib.sha256(f"{_SALT}:{password}".encode()).hexdigest()


# ── Token verification dependency ──
# Tokens are volatile (in-memory). Users are persisted in DB.


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency that extracts and validates the Bearer token."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = storage.tokens.get(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await repo.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


# ── Routes ──


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await repo.get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user_id = storage.generate_id()
    user = {
        "id": user_id,
        "username": body.username,
        "password_hash": _hash_password(body.password),
    }
    await repo.save_user(db, user)
    return UserResponse(id=user_id, username=body.username)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    pw_hash = _hash_password(body.password)
    user = await repo.get_user_by_username(db, body.username)
    if user and user.get("password_hash") == pw_hash:
        token = secrets.token_urlsafe(32)
        storage.tokens[token] = user["id"]
        return LoginResponse(token=token, username=user["username"], id=user["id"])

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], username=user["username"])
