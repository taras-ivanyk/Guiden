"""Race prep router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_valid_access_token
from backend.models.profile import UserProfileRequest
from src.profile import UserProfile
from src.skills import race_prep_skill, expand_race_section_skill
from src.logging_config import logger

router = APIRouter()


class RacePrepRequest(BaseModel):
    profile: UserProfileRequest
    race_inputs: dict


class RacePrepResponse(BaseModel):
    plan: str


class RaceExpandRequest(BaseModel):
    current_plan: str
    question: str


class RaceExpandResponse(BaseModel):
    expansion: str


@router.post("/prep", response_model=RacePrepResponse)
def race_prep(
    body: RacePrepRequest,
    access_token: str = Depends(get_valid_access_token),
) -> RacePrepResponse:
    """Generate a high-level phased race preparation plan."""
    logger.info("[api/race] prep")
    profile = UserProfile(
        age=body.profile.age,
        ftp=body.profile.ftp,
        goal=body.profile.goal,
        experience=body.profile.experience,
        injuries=body.profile.injuries,
    )
    try:
        result = race_prep_skill(profile, body.race_inputs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return RacePrepResponse(plan=result)


@router.post("/expand", response_model=RaceExpandResponse)
def race_expand(
    body: RaceExpandRequest,
    access_token: str = Depends(get_valid_access_token),
) -> RaceExpandResponse:
    """Expand a specific phase of a race prep plan."""
    logger.info("[api/race] expand")
    try:
        result = expand_race_section_skill(body.current_plan, body.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return RaceExpandResponse(expansion=result)
