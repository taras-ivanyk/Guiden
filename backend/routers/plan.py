"""Plan router — next session and multi-week training plan."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_valid_access_token
from backend.models.plan import (
    MultiWeekPlanResponse,
    NextSessionResponse,
    PlanRequest,
    SessionResponse,
    WeekResponse,
)
from src.profile import UserProfile
from src.skills import next_session_skill, training_plan_skill
from src.logging_config import logger

router = APIRouter()


def _build_profile(req: PlanRequest) -> UserProfile:
    return UserProfile(
        age=req.profile.age,
        ftp=req.profile.ftp,
        goal=req.goal or req.profile.goal,
        experience=req.experience or req.profile.experience,
        injuries=req.injuries or req.profile.injuries,
    )


def _build_plan_inputs(req: PlanRequest) -> dict:
    return {
        "calendar": [s.model_dump() for s in req.calendar],
        "goal": req.goal,
        "experience": req.experience,
        "sleep_hours": req.sleep_hours,
        "injuries": req.injuries,
        "weeks": req.weeks,
    }


def _build_availability(req: PlanRequest) -> dict:
    """Convert calendar list to the dict format expected by build_plan_context."""
    return {
        slot.day: {
            "start": slot.start,
            "end": slot.end,
            "duration_min": slot.duration_min,
        }
        for slot in req.calendar
    }


@router.post("/next-session", response_model=NextSessionResponse)
def next_session(
    body: PlanRequest,
    access_token: str = Depends(get_valid_access_token),
) -> NextSessionResponse:
    """Recommend one specific next training session."""
    logger.info("[api/plan] next-session")
    profile = _build_profile(body)
    plan_inputs = _build_plan_inputs(body)
    availability = _build_availability(body)
    recent = body.recent_summary or {}

    try:
        result = next_session_skill(profile, plan_inputs, recent, availability)
    except Exception as exc:
        logger.error(f"[api/plan] next_session error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    return NextSessionResponse(next_session=result)


@router.post("/multi-week", response_model=MultiWeekPlanResponse)
def multi_week_plan(
    body: PlanRequest,
    access_token: str = Depends(get_valid_access_token),
) -> MultiWeekPlanResponse:
    """Generate a full multi-week training plan as structured JSON."""
    logger.info(f"[api/plan] multi-week — {body.weeks} weeks")
    profile = _build_profile(body)
    plan_inputs = _build_plan_inputs(body)
    availability = _build_availability(body)
    recent = body.recent_summary or {}

    try:
        result = training_plan_skill(profile, plan_inputs, recent, availability)
    except Exception as exc:
        logger.error(f"[api/plan] training_plan error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    # result is list[dict] or str
    if isinstance(result, str):
        raise HTTPException(
            status_code=422,
            detail="Plan generation returned non-JSON output. Try again.",
        )

    weeks = []
    for w in result:
        sessions = [
            SessionResponse(
                day=s.get("day", ""),
                type=s.get("type", ""),
                duration_min=int(s.get("duration_min", 0)),
                intensity=s.get("intensity", ""),
                start_time=s.get("start_time"),
            )
            for s in w.get("sessions", [])
        ]
        weeks.append(WeekResponse(
            week_num=w.get("week_num", 0),
            focus=w.get("focus", ""),
            total_hours=float(w.get("total_hours", 0)),
            sessions=sessions,
            recovery_days=w.get("recovery_days", []),
        ))

    return MultiWeekPlanResponse(plan=weeks)
