"""Shared FastAPI dependencies — JWT decoding, Strava token extraction."""
from __future__ import annotations

import os
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.middleware.auth import decode_jwt

_bearer = HTTPBearer()


def get_strava_tokens(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Extract and validate Strava tokens from the request JWT.

    Raises:
        HTTPException 401: If the JWT is missing, invalid, or expired.

    Returns:
        Dict with ``access_token``, ``refresh_token``, ``expires_at``.
    """
    payload = decode_jwt(creds.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please reconnect Strava.",
        )
    return {
        "access_token": payload["strava_access_token"],
        "refresh_token": payload["strava_refresh_token"],
        "expires_at": payload["strava_expires_at"],
    }


def get_valid_access_token(
    tokens: dict = Depends(get_strava_tokens),
) -> str:
    """Return a valid Strava access token, refreshing if needed.

    If the stored access token has expired, uses the refresh token to
    obtain a new one from Strava and returns the fresh access token.

    Raises:
        HTTPException 401: If token refresh fails.

    Returns:
        Valid Strava access token string.
    """
    from src.strava import _do_token_refresh
    from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

    if tokens["expires_at"] > time.time() + 60:
        return tokens["access_token"]

    try:
        new_tokens = _do_token_refresh(
            tokens["refresh_token"],
            STRAVA_CLIENT_ID,
            STRAVA_CLIENT_SECRET,
        )
        return new_tokens["access_token"]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {exc}",
        )
