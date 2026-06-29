"""Auth request/response models."""
from __future__ import annotations

from pydantic import BaseModel


class StravaCallbackRequest(BaseModel):
    code: str


class AthleteInfo(BaseModel):
    id: int | None = None
    firstname: str = ""
    lastname: str = ""
    profile: str = ""


class AuthResponse(BaseModel):
    """Returned after successful Strava OAuth code exchange."""

    jwt: str
    athlete: AthleteInfo


class StravaAuthUrlResponse(BaseModel):
    url: str
