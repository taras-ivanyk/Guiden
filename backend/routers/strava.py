"""Strava data router — activities list, detail, recent summary."""
from __future__ import annotations

from datetime import date

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.deps import get_valid_access_token
from backend.models.activity import (
    ActivityDetailResponse,
    ActivitySummaryResponse,
    LapResponse,
    RecentSummaryResponse,
)
from src.logging_config import logger

router = APIRouter()

_STRAVA_BASE = "https://www.strava.com/api/v3"
_CYCLING_TYPES = {
    "Ride", "VirtualRide", "EBikeRide", "Velomobile",
    "Handcycle", "GravelRide", "MountainBikeRide",
}


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


@router.get("/activities", response_model=list[ActivitySummaryResponse])
def list_activities(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
    min_dist: float = Query(0.0, ge=0),
    max_dist: float = Query(0.0, ge=0, description="0 = no limit"),
    min_dur: float = Query(0.0, ge=0),
    max_dur: float = Query(0.0, ge=0, description="0 = no limit"),
    access_token: str = Depends(get_valid_access_token),
) -> list[ActivitySummaryResponse]:
    """Fetch cycling activities within a date range with optional filters."""
    from datetime import datetime, time as _time

    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    after = int(datetime.combine(start_date, _time.min).timestamp())
    before = int(datetime.combine(end_date, _time.max).timestamp())

    activities: list[ActivitySummaryResponse] = []
    page = 1

    while True:
        resp = requests.get(
            f"{_STRAVA_BASE}/athlete/activities",
            headers=_headers(access_token),
            params={"after": after, "before": before, "per_page": 100, "page": page},
            timeout=15,
        )
        if resp.status_code == 401:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Strava token invalid.")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Strava error: {resp.text}")

        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break

        for a in batch:
            atype = a.get("sport_type") or a.get("type", "")
            if atype not in _CYCLING_TYPES:
                continue
            dist = round(a.get("distance", 0) / 1000, 2)
            dur = round(a.get("moving_time", 0) / 60, 1)
            if dist < min_dist:
                continue
            if max_dist > 0 and dist > max_dist:
                continue
            if dur < min_dur:
                continue
            if max_dur > 0 and dur > max_dur:
                continue
            activities.append(ActivitySummaryResponse(
                id=str(a["id"]),
                name=a.get("name", ""),
                type=atype,
                date=a.get("start_date_local", "")[:10],
                distance_km=dist,
                moving_time_min=dur,
                avg_hr=a.get("average_heartrate"),
                max_hr=a.get("max_heartrate"),
                avg_watts=a.get("average_watts"),
            ))
        page += 1

    logger.info(f"[api/strava] list_activities → {len(activities)} results")
    return activities


@router.get("/activity/{activity_id}", response_model=ActivityDetailResponse)
def get_activity(
    activity_id: str,
    access_token: str = Depends(get_valid_access_token),
) -> ActivityDetailResponse:
    """Fetch full detail for one activity, including laps."""
    resp = requests.get(
        f"{_STRAVA_BASE}/activities/{activity_id}",
        headers=_headers(access_token),
        timeout=15,
    )
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Strava token invalid.")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Activity not found.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Strava error: {resp.text}")

    a = resp.json()
    laps = [
        LapResponse(
            lap_num=lap.get("lap_index", 0),
            distance_km=round(lap.get("distance", 0) / 1000, 2),
            time_min=round(lap.get("elapsed_time", 0) / 60, 1),
            avg_watts=lap.get("average_watts"),
            avg_hr=lap.get("average_heartrate"),
            avg_speed_kmh=round(lap.get("average_speed", 0) * 3.6, 1),
        )
        for lap in a.get("laps", [])
    ]
    return ActivityDetailResponse(
        id=str(a["id"]),
        name=a.get("name", ""),
        type=a.get("sport_type") or a.get("type", ""),
        date=a.get("start_date_local", "")[:10],
        distance_km=round(a.get("distance", 0) / 1000, 2),
        moving_time_min=round(a.get("moving_time", 0) / 60, 1),
        avg_hr=a.get("average_heartrate"),
        max_hr=a.get("max_heartrate"),
        avg_watts=a.get("average_watts"),
        start_latlng=a.get("start_latlng"),
        total_elevation_gain=a.get("total_elevation_gain"),
        description=a.get("description", ""),
        laps=laps,
    )


@router.get("/recent-summary", response_model=RecentSummaryResponse)
def recent_summary(
    days: int = Query(14, ge=1, le=90),
    access_token: str = Depends(get_valid_access_token),
) -> RecentSummaryResponse:
    """Aggregate cycling stats for the last N days."""
    from datetime import datetime, timedelta, time as _time

    cutoff_dt = datetime.utcnow() - timedelta(days=days)
    after = int(datetime.combine(cutoff_dt.date(), _time.min).timestamp())

    resp = requests.get(
        f"{_STRAVA_BASE}/athlete/activities",
        headers=_headers(access_token),
        params={"after": after, "per_page": 100},
        timeout=15,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Strava error: {resp.text}")

    raw = resp.json()
    recent = [
        a for a in raw
        if (a.get("sport_type") or a.get("type", "")) in _CYCLING_TYPES
    ]

    if not recent:
        return RecentSummaryResponse(
            days=days, num_rides=0, total_hours=0.0,
            total_distance_km=0.0, avg_power=None, num_hard_sessions=0,
        )

    total_min = sum(round(a.get("moving_time", 0) / 60, 1) for a in recent)
    total_km = sum(round(a.get("distance", 0) / 1000, 2) for a in recent)
    powers = [a["average_watts"] for a in recent if a.get("average_watts")]
    avg_power = round(sum(powers) / len(powers), 1) if powers else None
    hard = sum(
        1 for a in recent
        if a.get("moving_time", 0) / 60 > 60
        or (a.get("average_watts") and avg_power and a["average_watts"] > avg_power * 1.1)
    )
    return RecentSummaryResponse(
        days=days,
        num_rides=len(recent),
        total_hours=round(total_min / 60, 1),
        total_distance_km=round(total_km, 1),
        avg_power=avg_power,
        num_hard_sessions=hard,
    )
