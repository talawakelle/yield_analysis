from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import Header, HTTPException

from app.core.config import settings


@dataclass
class AdminSession:
    token: str
    username: str
    expires_at: datetime


_SESSIONS: dict[str, AdminSession] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_admin_session(username: str) -> AdminSession:
    token = secrets.token_urlsafe(32)
    session = AdminSession(
        token=token,
        username=username,
        expires_at=_utcnow() + timedelta(hours=settings.admin_token_expiry_hours),
    )
    _SESSIONS[token] = session
    return session


def prune_expired_sessions() -> None:
    now = _utcnow()
    expired = [token for token, session in _SESSIONS.items() if session.expires_at <= now]
    for token in expired:
        _SESSIONS.pop(token, None)


def validate_credentials(username: str, password: str) -> bool:
    return username == settings.admin_username and password == settings.admin_password


def get_session(token: str) -> Optional[AdminSession]:
    prune_expired_sessions()
    session = _SESSIONS.get(token)
    if not session:
        return None
    if session.expires_at <= _utcnow():
        _SESSIONS.pop(token, None)
        return None
    return session


def destroy_session(token: str) -> None:
    _SESSIONS.pop(token, None)


def _parse_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    value = authorization.strip()
    if not value:
        return None
    parts = value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return value


def require_admin(authorization: str | None = Header(default=None)) -> AdminSession:
    token = _parse_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing admin token.")
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token.")
    return session
