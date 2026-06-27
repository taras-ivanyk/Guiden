"""Strava API client for the AI Endurance Coach."""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

STRAVA_BASE = "https://www.strava.com/api/v3"


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


def get_recent_activities(limit: int = 10) -> list[dict]:
    """Fetch a list of the athlete's recent activities.

    Args:
        limit: Maximum number of activities to return.

    Returns:
        List of activity summary dicts with keys:
        id, name, type, date, distance_km, moving_time_min,
        avg_hr, max_hr, avg_watts, start_latlng.

    Raises:
        RuntimeError: On 401 (token expired) or other API errors.
    """
    resp = requests.get(
        f"{STRAVA_BASE}/athlete/activities",
        headers=_headers(),
        params={"per_page": limit},
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
        activities.append(
            {
                "id": a["id"],
                "name": a.get("name", ""),
                "type": a.get("type", ""),
                "date": a.get("start_date_local", "")[:10],
                "distance_km": round(a.get("distance", 0) / 1000, 2),
                "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
                "avg_hr": a.get("average_heartrate"),
                "max_hr": a.get("max_heartrate"),
                "avg_watts": a.get("average_watts"),
                "start_latlng": a.get("start_latlng"),
            }
        )
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
        "type": a.get("type", ""),
        "date": a.get("start_date_local", "")[:10],
        "distance_km": round(a.get("distance", 0) / 1000, 2),
        "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
        "avg_hr": a.get("average_heartrate"),
        "max_hr": a.get("max_heartrate"),
        "avg_watts": a.get("average_watts"),
        "start_latlng": a.get("start_latlng"),
        "description": a.get("description", ""),
        "laps": laps,
    }
