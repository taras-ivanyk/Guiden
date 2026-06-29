"""Session detail router — on-demand full session expansion."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_valid_access_token
from backend.models.profile import UserProfileRequest
from src.profile import UserProfile
from src.skills import expand_session_skill
from src.logging_config import logger

router = APIRouter()


class SessionExpandRequest(BaseModel):
    week_num: int
    day: str
    session: dict
    profile: UserProfileRequest


class SessionExpandResponse(BaseModel):
    detail: str


@router.post("/expand", response_model=SessionExpandResponse)
def expand_session(
    body: SessionExpandRequest,
    access_token: str = Depends(get_valid_access_token),
) -> SessionExpandResponse:
    """Generate full session detail (warm-up, main set, cool-down, RPE, fueling)."""
    logger.info(f"[api/session] expand — week={body.week_num} day={body.day}")
    profile = UserProfile(
        age=body.profile.age,
        ftp=body.profile.ftp,
        goal=body.profile.goal,
        experience=body.profile.experience,
        injuries=body.profile.injuries,
    )
    try:
        result = expand_session_skill(body.week_num, body.day, body.session, profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return SessionExpandResponse(detail=result)
