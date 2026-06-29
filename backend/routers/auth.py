"""Auth router — Strava OAuth URL generation and code exchange."""
from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, status

from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
from src.strava import exchange_code_for_tokens, get_athlete_info
from backend.middleware.auth import create_jwt
from backend.models.auth import (
    AthleteInfo,
    AuthResponse,
    StravaAuthUrlResponse,
    StravaCallbackRequest,
)

router = APIRouter()

_REDIRECT_URI = "http://localhost:5173/auth/callback"
_SCOPE = "read,activity:read_all,profile:read_all"


@router.get("/strava/url", response_model=StravaAuthUrlResponse)
def get_strava_auth_url() -> StravaAuthUrlResponse:
    """Return the Strava OAuth authorization URL.

    The React app opens this URL in the browser. After the user approves,
    Strava redirects to REDIRECT_URI with ``?code=...``.
    """
    if not STRAVA_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STRAVA_CLIENT_ID not configured on the server.",
        )
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": _REDIRECT_URI,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": _SCOPE,
    }
    url = "https://www.strava.com/oauth/authorize?" + urlencode(params)
    return StravaAuthUrlResponse(url=url)


@router.post("/strava/callback", response_model=AuthResponse)
def strava_callback(body: StravaCallbackRequest) -> AuthResponse:
    """Exchange a Strava OAuth code for tokens and return a signed JWT.

    The React app calls this once after being redirected back from Strava.

    Args:
        body: Contains the one-time ``code`` from the redirect query param.

    Returns:
        JWT (embed in Authorization header for all subsequent requests)
        and basic athlete info.

    Raises:
        HTTPException 400: If the code exchange fails.
        HTTPException 503: If Strava credentials are not configured.
    """
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strava credentials not configured on the server.",
        )
    try:
        tokens = exchange_code_for_tokens(body.code, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET)
        athlete_raw = get_athlete_info(tokens["access_token"])
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    jwt_token = create_jwt(tokens, athlete_raw)
    athlete = AthleteInfo(
        id=athlete_raw.get("id"),
        firstname=athlete_raw.get("firstname", ""),
        lastname=athlete_raw.get("lastname", ""),
        profile=athlete_raw.get("profile", ""),
    )
    return AuthResponse(jwt=jwt_token, athlete=athlete)
