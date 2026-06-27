"""Strava API client for the AI Endurance Coach."""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

STRAVA_BASE = "https://www.strava.com/api/v3"

# Strava sport types that count as cycling
CYCLING_SPORT_TYPES = {
    "Ride", "VirtualRide", "EBikeRide", "Velomobile",
    "Handcycle", "GravelRide", "MountainBikeRide",
}


def _get_token() -> str:
    """Refresh and return a valid Strava access token.

    Raises:
        EnvironmentError: If required env vars are missing.
        RuntimeError: If the token refresh fails.
    """
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError(
            "Missing STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, or STRAVA_REFRESH_TOKEN in .env"
        )

    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp.text}")

    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in Strava response.")
    return token


def _headers() -> dict:
    """Return Authorization headers with a fresh token."""
    return {"Authorization": f"Bearer {_get_token()}"}


def get_recent_activities(limit: Optional[int] = None) -> list[dict]:
    """Fetch recent cycling activities from Strava.

    Args:
        limit: Max cycling activities to return. Defaults to the
            TOP_K_ACTIVITIES environment variable (default 10).

    Returns:
        List of cycling activity summary dicts with keys:
        id, name, type, date, distance_km, moving_time_min,
        avg_hr, max_hr, avg_watts, start_latlng, total_elevation_gain.

    Raises:
        RuntimeError: On 401 (token expired) or other API errors.
    """
    top_k = limit if limit is not None else int(os.getenv("TOP_K_ACTIVITIES", "10"))
    # Fetch more raw activities to account for non-cycling filtering
    fetch_count = min(top_k * 5, 200)

    resp = requests.get(
        f"{STRAVA_BASE}/athlete/activities",
        headers=_headers(),
        params={"per_page": fetch_count},
        timeout=15,
    )

    if resp.status_code == 401:
        raise RuntimeError(
            "Strava token expired or unauthorized. "
            "Re-run oauth_setup.py to get a new refresh token."
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Strava activities error ({resp.status_code}): {resp.text}")

    raw = resp.json()
    if not isinstance(raw, list):
        raise RuntimeError(f"Unexpected Strava response: {raw}")

    activities = []
    for a in raw:
        activity_type = a.get("sport_type") or a.get("type", "")
        if activity_type not in CYCLING_SPORT_TYPES:
            continue
        activities.append(
            {
                "id": a["id"],
                "name": a.get("name", ""),
                "type": activity_type,
                "date": a.get("start_date_local", "")[:10],
                "distance_km": round(a.get("distance", 0) / 1000, 2),
                "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
                "avg_hr": a.get("average_heartrate"),
                "max_hr": a.get("max_heartrate"),
                "avg_watts": a.get("average_watts"),
                "start_latlng": a.get("start_latlng"),
                "total_elevation_gain": a.get("total_elevation_gain"),
            }
        )
        if len(activities) >= top_k:
            break
    return activities


def get_activity_detail(activity_id: int) -> dict:
    """Fetch full detail for one activity, including laps.

    Args:
        activity_id: Strava activity ID.

    Returns:
        Dict with all summary fields plus a `laps` list.
        Each lap has: lap_num, distance_km, time_min,
        avg_watts, avg_hr, avg_speed_kmh.

    Raises:
        RuntimeError: On 401 or other API errors.
    """
    resp = requests.get(
        f"{STRAVA_BASE}/activities/{activity_id}",
        headers=_headers(),
        timeout=15,
    )

    if resp.status_code == 401:
        raise RuntimeError(
            "Strava token expired or unauthorized. "
            "Re-run oauth_setup.py to get a new refresh token."
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Strava activity detail error ({resp.status_code}): {resp.text}"
        )

    a = resp.json()

    laps = []
    for lap in a.get("laps", []):
        laps.append(
            {
                "lap_num": lap.get("lap_index", 0),
                "distance_km": round(lap.get("distance", 0) / 1000, 2),
                "time_min": round(lap.get("elapsed_time", 0) / 60, 1),
                "avg_watts": lap.get("average_watts"),
                "avg_hr": lap.get("average_heartrate"),
                "avg_speed_kmh": round(lap.get("average_speed", 0) * 3.6, 1),
            }
        )

    return {
        "id": a["id"],
        "name": a.get("name", ""),
        "type": a.get("sport_type") or a.get("type", ""),
        "date": a.get("start_date_local", "")[:10],
        "distance_km": round(a.get("distance", 0) / 1000, 2),
        "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
        "avg_hr": a.get("average_heartrate"),
        "max_hr": a.get("max_heartrate"),
        "avg_watts": a.get("average_watts"),
        "start_latlng": a.get("start_latlng"),
        "total_elevation_gain": a.get("total_elevation_gain"),
        "description": a.get("description", ""),
        "laps": laps,
    }


def get_recent_summary(days: int = 14) -> dict:
    """Aggregate cycling stats for recent activities.

    Args:
        days: Number of days to look back.

    Returns:
        Dict with keys: total_hours (float), avg_power (float|None),
        num_hard_sessions (int), num_rides (int),
        total_distance_km (float), days (int).
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    activities = get_recent_activities(limit=50)
    recent = [a for a in activities if a["date"] >= cutoff]

    if not recent:
        return {
            "total_hours": 0.0,
            "avg_power": None,
            "num_hard_sessions": 0,
            "num_rides": 0,
            "total_distance_km": 0.0,
            "days": days,
        }

    total_min = sum(a["moving_time_min"] for a in recent)
    total_km = sum(a["distance_km"] for a in recent)
    powers = [a["avg_watts"] for a in recent if a.get("avg_watts")]
    avg_power = round(sum(powers) / len(powers), 1) if powers else None

    # Hard session heuristic: >60 min or power significantly above the period average
    hard = sum(
        1 for a in recent
        if a["moving_time_min"] > 60
        or (a.get("avg_watts") and avg_power and a["avg_watts"] > avg_power * 1.1)
    )

    return {
        "total_hours": round(total_min / 60, 1),
        "avg_power": avg_power,
        "num_hard_sessions": hard,
        "num_rides": len(recent),
        "total_distance_km": round(total_km, 1),
        "days": days,
    }
