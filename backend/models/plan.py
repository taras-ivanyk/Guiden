"""Training plan request/response models."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from backend.models.profile import UserProfileRequest


class CalendarSlot(BaseModel):
    """A single training window in the weekly calendar."""

    day: str = Field(..., description="Full day name e.g. 'Tuesday'")
    start: str = Field(..., description="Start time HH:MM")
    end: str = Field(..., description="End time HH:MM")
    duration_min: int = Field(..., gt=0, description="Window duration in minutes")


class PlanRequest(BaseModel):
    """Request body for next-session and multi-week plan endpoints."""

    profile: UserProfileRequest
    calendar: list[CalendarSlot] = Field(
        ..., min_length=1, description="Selected training days — single source of truth"
    )
    goal: str = ""
    experience: str = ""
    sleep_hours: float = Field(7.5, ge=4.0, le=10.0)
    injuries: str = ""
    weeks: int = Field(4, ge=1, le=12)
    recent_summary: Optional[dict] = None

    model_config = {"json_schema_extra": {"example": {
        "profile": {"age": 28, "ftp": 280, "goal": "Improve FTP", "experience": "Intermediate — training 3-4 times/week", "injuries": ""},
        "calendar": [{"day": "Tuesday", "start": "07:00", "end": "09:00", "duration_min": 120}],
        "goal": "Improve FTP by 20W",
        "experience": "Intermediate — training 3-4 times/week",
        "sleep_hours": 7.5,
        "injuries": "",
        "weeks": 4,
    }}}


class SessionResponse(BaseModel):
    day: str
    type: str
    duration_min: int
    intensity: str
    start_time: Optional[str] = None


class WeekResponse(BaseModel):
    week_num: int
    focus: str
    total_hours: float
    sessions: list[SessionResponse]
    recovery_days: list[str]


class MultiWeekPlanResponse(BaseModel):
    plan: list[WeekResponse]


class NextSessionResponse(BaseModel):
    next_session: str
