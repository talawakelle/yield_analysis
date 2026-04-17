
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Request

from app.core.config import settings

USERNAME_HEADERS = (
    "x-auth-user",
    "x-forwarded-user",
    "x-remote-user",
    "remote-user",
    "x-user",
    "x-username",
    "x-auth-email",
    "x-email",
)
USERNAME_QUERY_KEYS = ("username", "user", "email", "login")
KNOWN_PLANTATIONS = ("TTEL", "KVPL", "HPL")


@dataclass(slots=True)
class AccessContext:
    username: str | None
    display_name: str | None
    role: str
    accessible_plantations: list[str]
    accessible_estates: list[str]
    resolved_estate: str | None
    access_mode: str
    access_message: str | None
    source: str


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return "".join(char.lower() for char in str(value) if char.isalnum())


def _extract_username(request: Request) -> tuple[str | None, str]:
    for key in USERNAME_QUERY_KEYS:
        value = request.query_params.get(key)
        if value and value.strip():
            return value.strip(), f"query:{key}"
    for key in USERNAME_HEADERS:
        value = request.headers.get(key)
        if value and value.strip():
            return value.strip(), f"header:{key}"
    return None, "anonymous"


def _normalize_plantation(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = str(value).strip().upper()
    if cleaned in KNOWN_PLANTATIONS:
        return cleaned
    return None


def _read_access_records() -> list[dict[str, Any]]:
    path = Path(settings.access_file_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    records: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for key in ("admins", "users", "entries"):
            if isinstance(payload.get(key), list):
                for item in payload[key]:
                    if isinstance(item, dict):
                        records.append(item)
    return records


def _match_record(records: list[dict[str, Any]], username: str | None) -> dict[str, Any] | None:
    if not username:
        return None

    normalized_username = _normalize_token(username)
    if not normalized_username:
        return None

    for row in records:
        keys = [
            row.get("username"),
            row.get("user"),
            row.get("email"),
            row.get("login"),
            row.get("alias"),
        ]
        aliases = row.get("aliases")
        if isinstance(aliases, list):
            keys.extend(aliases)

        if any(_normalize_token(str(item)) == normalized_username for item in keys if item):
            return row
    return None


def _all_plantations(df) -> list[str]:
    if df is None or "plantation" not in df.columns:
        return list(KNOWN_PLANTATIONS)
    values = {str(item).strip().upper() for item in df["plantation"].tolist() if str(item).strip()}
    return [item for item in KNOWN_PLANTATIONS if item in values] or list(KNOWN_PLANTATIONS)


def _all_estates(df) -> list[str]:
    if df is None or "estate" not in df.columns:
        return []
    values = sorted({str(item).strip() for item in df["estate"].tolist() if str(item).strip()}, key=lambda x: x.lower())
    return values


def _estates_for_plantations(df, plantations: list[str]) -> list[str]:
    if df is None or df.empty or "estate" not in df.columns or "plantation" not in df.columns:
        return []
    allowed = {str(item).strip().upper() for item in plantations if str(item).strip()}
    if not allowed:
        return []
    matches = df[df["plantation"].astype(str).str.upper().isin(allowed)]
    return sorted({str(item).strip() for item in matches["estate"].tolist() if str(item).strip()}, key=lambda x: x.lower())


def resolve_access_context(request: Request, df=None) -> AccessContext:
    username, source = _extract_username(request)
    if not username:
        return AccessContext(
            username=None,
            display_name=None,
            role="anonymous",
            accessible_plantations=[],
            accessible_estates=[],
            resolved_estate=None,
            access_mode="restricted",
            access_message="Open this project through the central login portal.",
            source=source,
        )

    records = _read_access_records()
    mapping = _match_record(records, username)
    if not mapping:
        return AccessContext(
            username=username,
            display_name=None,
            role="viewer",
            accessible_plantations=[],
            accessible_estates=[],
            resolved_estate=None,
            access_mode="restricted",
            access_message=f"No plantation access mapping found for user '{username}'.",
            source=f"{source}|restricted",
        )

    role = str(mapping.get("role") or "viewer").strip().lower() or "viewer"
    display_name = mapping.get("display_name") or mapping.get("name")

    all_plantations = _all_plantations(df)
    all_estates = _all_estates(df)

    estates_raw = mapping.get("estates")
    accessible_estates: list[str] = []
    if isinstance(estates_raw, list):
        accessible_estates = [str(item).strip() for item in estates_raw if str(item).strip()]
    elif mapping.get("estate"):
        accessible_estates = [str(mapping.get("estate")).strip()]

    plantations_raw = mapping.get("plantations")
    accessible_plantations: list[str] = []
    if isinstance(plantations_raw, list):
        accessible_plantations = [
            normalized
            for item in plantations_raw
            if (normalized := _normalize_plantation(item))
        ]
    else:
        single = _normalize_plantation(mapping.get("plantation"))
        if single:
            accessible_plantations = [single]

    # Plantation dashboard visibility rules:
    # - ADMIN and MD can see every plantation / estate
    # - Plantation CEOs see all estates inside only their mapped plantation
    # - Estate users are locked to their mapped estate, and the UI can still offer
    #   an "All Plantations" view that remains limited to their allowed scope.
    if role in {"md", "admin"}:
        accessible_plantations = list(all_plantations)
        accessible_estates = list(all_estates)
    elif role == "ceo":
        if not accessible_plantations and all_plantations:
            accessible_plantations = list(all_plantations)
        if df is not None and not df.empty:
            accessible_estates = _estates_for_plantations(df, accessible_plantations)

    accessible_plantations = list(dict.fromkeys(accessible_plantations))
    accessible_estates = list(dict.fromkeys(accessible_estates))

    if not accessible_plantations and accessible_estates and df is not None and not df.empty:
        matches = df[df["estate"].astype(str).isin(accessible_estates)]
        accessible_plantations = sorted(
            {str(item).strip().upper() for item in matches["plantation"].tolist() if str(item).strip()},
            key=lambda x: x.lower(),
        )

    resolved_estate = accessible_estates[0] if role not in {"md", "admin", "ceo"} and len(accessible_estates) == 1 else None
    access_mode = "locked" if resolved_estate else "scoped"

    if not accessible_plantations and settings.access_strict_mode:
        access_mode = "restricted"

    return AccessContext(
        username=username,
        display_name=str(display_name).strip() if display_name else None,
        role=role,
        accessible_plantations=accessible_plantations,
        accessible_estates=accessible_estates,
        resolved_estate=resolved_estate,
        access_mode=access_mode,
        access_message=None if access_mode != "restricted" else "No accessible plantations found for this account.",
        source=f"{source}|mapping",
    )


def serialize_access_context(access: AccessContext) -> dict[str, Any]:
    return {
        "username": access.username,
        "display_name": access.display_name,
        "role": access.role,
        "accessible_plantations": access.accessible_plantations,
        "accessible_estates": access.accessible_estates,
        "resolved_estate": access.resolved_estate,
        "access_mode": access.access_mode,
        "access_message": access.access_message,
        "source": access.source,
    }


def apply_access_scope(df, access: AccessContext):
    if df is None:
        return df
    if access.access_mode == "restricted":
        return df.iloc[0:0].copy()

    out = df.copy()

    if access.role not in {"ceo", "md", "admin"} and access.accessible_plantations:
        out = out[out["plantation"].astype(str).isin(access.accessible_plantations)]

    if access.role not in {"ceo", "md", "admin"} and access.accessible_estates:
        out = out[out["estate"].astype(str).isin(access.accessible_estates)]

    return out.reset_index(drop=True)
