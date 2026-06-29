"""JWT creation and validation for stateless auth."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt

_ALGORITHM = "HS256"


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET is not set in .env — required for the FastAPI backend."
        )
    return secret


def create_jwt(strava_tokens: dict, athlete: dict) -> str:
    """Sign a JWT containing the user's Strava tokens and athlete info.

    The JWT is stateless — the backend stores nothing server-side.
    Strava access tokens expire after 6h; the JWT itself does not expire
    (the access token expiry inside the payload is used instead).

    Args:
        strava_tokens: Full Strava token response dict (access_token,
            refresh_token, expires_at).
        athlete: Basic athlete info dict (id, firstname, lastname).

    Returns:
        Signed JWT string.
    """
    payload: dict[str, Any] = {
        "strava_access_token": strava_tokens["access_token"],
        "strava_refresh_token": strava_tokens["refresh_token"],
        "strava_expires_at": strava_tokens["expires_at"],
        "athlete_id": athlete.get("id"),
        "athlete_firstname": athlete.get("firstname", ""),
        "athlete_lastname": athlete.get("lastname", ""),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and verify a JWT.

    Args:
        token: JWT string from the Authorization header.

    Returns:
        Decoded payload dict, or None if the token is invalid.
    """
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except JWTError:
        return None
