"""Activity request/response models."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class LapResponse(BaseModel):
    lap_num: int
    distance_km: float
    time_min: float
    avg_watts: Optional[int] = None
    avg_hr: Optional[int] = None
    avg_speed_kmh: Optional[float] = None


class ActivitySummaryResponse(BaseModel):
    id: str
    name: str
    type: str
    date: str
    distance_km: float
    moving_time_min: float
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    avg_watts: Optional[int] = None


class ActivityDetailResponse(ActivitySummaryResponse):
    start_latlng: Optional[list[float]] = None
    total_elevation_gain: Optional[float] = None
    description: str = ""
    laps: list[LapResponse] = Field(default_factory=list)


class RecentSummaryResponse(BaseModel):
    days: int
    num_rides: int
    total_hours: float
    total_distance_km: float
    avg_power: Optional[float] = None
    num_hard_sessions: int


class ActivitiesQueryParams(BaseModel):
    """Query parameters for the activities list endpoint."""
    start: str = Field(..., description="Start date YYYY-MM-DD")
    end: str = Field(..., description="End date YYYY-MM-DD")
    min_dist: float = Field(0.0, ge=0)
    max_dist: float = Field(0.0, ge=0, description="0 = no limit")
    min_dur: float = Field(0.0, ge=0)
    max_dur: float = Field(0.0, ge=0, description="0 = no limit")
