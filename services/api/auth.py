from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.api.config import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_users_db: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def register_user(user_id: str, password: str, role: str = "student") -> dict:
    if user_id in _users_db:
        raise ValueError("User already exists")
    _users_db[user_id] = {
        "user_id": user_id,
        "password_hash": hash_password(password),
        "role": role,
    }
    return {"user_id": user_id, "role": role}


def authenticate_user(user_id: str, password: str) -> dict | None:
    user = _users_db.get(user_id)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> dict | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return {"user_id": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_role(*roles: str):
    def dependency(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    ) -> dict:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        user = get_current_user(credentials)
        if user is None or user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency
