"""Strava API client for the AI Endurance Coach."""

import os
import time
from datetime import datetime, timedelta, date, time as _time
from typing import Optional

import requests
from dotenv import load_dotenv

from src.logging_config import logger

load_dotenv()

STRAVA_BASE = "https://www.strava.com/api/v3"

# Strava sport types that count as cycling
CYCLING_SPORT_TYPES = {
    "Ride", "VirtualRide", "EBikeRide", "Velomobile",
    "Handcycle", "GravelRide", "MountainBikeRide",
}


def _do_token_refresh(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Exchange a refresh token for a fresh Strava token bundle.

    Args:
        refresh_token: Current Strava refresh token.
        client_id: Strava app client ID.
        client_secret: Strava app client secret.

    Returns:
        Full token response dict (access_token, refresh_token, expires_at, ...).

    Raises:
        RuntimeError: If the refresh request fails.
    """
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
    data = resp.json()
    if not data.get("access_token"):
        raise RuntimeError("No access_token in Strava refresh response.")
    return data


def _get_token() -> str:
    """Return a valid Strava access token.

    Priority order:
      1. Streamlit session state (``strava_tokens``) — set after UI OAuth flow.
         Automatically refreshes if the access token has expired.
      2. Environment variables / .env — developer / legacy fallback.

    Raises:
        EnvironmentError: If no credentials are available.
        RuntimeError: If token refresh fails.
    """
    from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN
    client_id = STRAVA_CLIENT_ID or os.getenv("STRAVA_CLIENT_ID", "")
    client_secret = STRAVA_CLIENT_SECRET or os.getenv("STRAVA_CLIENT_SECRET", "")

    # ── 1. Session-stored tokens (UI OAuth flow) ─────────────────────────────
    try:
        import streamlit as st
        tokens = st.session_state.get("strava_tokens")
        if tokens and isinstance(tokens, dict):
            if tokens.get("expires_at", 0) > time.time() + 60:
                logger.debug("[strava] Using session access token (valid)")
                return tokens["access_token"]
            # Access token expired — use stored refresh token
            session_refresh = tokens.get("refresh_token")
            if session_refresh and client_id and client_secret:
                logger.info("[strava] Session token expired — auto-refreshing")
                new_tokens = _do_token_refresh(session_refresh, client_id, client_secret)
                st.session_state["strava_tokens"] = {**tokens, **new_tokens}
                return new_tokens["access_token"]
    except Exception:
        pass  # Not in a Streamlit context, or session read failed

    # ── 2. Fallback: .env refresh token ─────────────────────────────────────
    refresh_token = STRAVA_REFRESH_TOKEN or os.getenv("STRAVA_REFRESH_TOKEN", "")
    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError(
            "Not connected to Strava. "
            "Click \u2018Connect with Strava\u2019 in the sidebar, "
            "or set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN in .env"
        )
    logger.info("[strava] Using .env refresh token")
    env_tokens = _do_token_refresh(refresh_token, client_id, client_secret)
    return env_tokens["access_token"]


def _headers() -> dict:
    """Return Authorization headers with a fresh token."""
    return {"Authorization": f"Bearer {_get_token()}"}


def get_recent_activities(limit: Optional[int] = None) -> list[dict]:
    """Fetch recent cycling activities from Strava.

    Args:
        limit: Max cycling activities to return. Defaults to TOP_K_ACTIVITIES env var.

    Returns:
        List of cycling activity summary dicts.

    Raises:
        RuntimeError: On 401 (token expired) or other API errors.
    """
    from src.config import TOP_K_ACTIVITIES as _TOP_K
    top_k = limit if limit is not None else _TOP_K
    fetch_count = min(top_k * 5, 200)

    logger.info(f"[strava] get_recent_activities — top_k={top_k}, fetch_count={fetch_count}")
    resp = requests.get(
        f"{STRAVA_BASE}/athlete/activities",
        headers=_headers(),
        params={"per_page": fetch_count},
        timeout=15,
    )

    if resp.status_code == 401:
        logger.error("[strava] 401 — token expired")
        raise RuntimeError(
            "Strava token expired or unauthorized. "
            "Re-run scripts/tools/oauth_setup.py to get a new refresh token."
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

    logger.info(f"[strava] get_recent_activities → {len(activities)} cycling activities returned")
    return activities


def get_activities_in_range(start_date: date, end_date: date) -> list[dict]:
    """Fetch ALL cycling activities within a date range using Strava epoch params.

    Handles Strava pagination automatically — loops until the API returns empty.
    Uses start_date_local for accurate local-time filtering.

    Args:
        start_date: First day of the range (inclusive).
        end_date: Last day of the range (inclusive).

    Returns:
        List of cycling activity summary dicts.

    Raises:
        RuntimeError: On 401 or other API errors.
    """
    after_epoch = int(datetime.combine(start_date, _time.min).timestamp())
    before_epoch = int(datetime.combine(end_date, _time.max).timestamp())

    logger.info(
        f"[strava] get_activities_in_range — "
        f"start={start_date}, end={end_date}, "
        f"after_epoch={after_epoch}, before_epoch={before_epoch}"
    )

    activities: list[dict] = []
    page = 1

    while True:
        resp = requests.get(
            f"{STRAVA_BASE}/athlete/activities",
            headers=_headers(),
            params={
                "after": after_epoch,
                "before": before_epoch,
                "per_page": 100,
                "page": page,
            },
            timeout=15,
        )

        if resp.status_code == 401:
            logger.error("[strava] 401 — token expired")
            raise RuntimeError(
                "Strava token expired. Re-run scripts/tools/oauth_setup.py."
            )
        if resp.status_code != 200:
            raise RuntimeError(f"Strava error ({resp.status_code}): {resp.text}")

        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            logger.info(f"[strava] Pagination done at page {page}")
            break

        logger.info(f"[strava] Page {page} → {len(batch)} raw activities")
        for a in batch:
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
        page += 1

    logger.info(
        f"[strava] get_activities_in_range → {len(activities)} cycling activities "
        f"in {start_date} – {end_date}"
    )
    return activities


def get_activity_detail(activity_id: int) -> dict:
    """Fetch full detail for one activity, including laps.

    Args:
        activity_id: Strava activity ID.

    Returns:
        Dict with all summary fields plus a `laps` list.

    Raises:
        RuntimeError: On 401 or other API errors.
    """
    logger.info(f"[strava] get_activity_detail — id={activity_id}")
    resp = requests.get(
        f"{STRAVA_BASE}/activities/{activity_id}",
        headers=_headers(),
        timeout=15,
    )

    if resp.status_code == 401:
        logger.error("[strava] 401 — token expired (get_activity_detail)")
        raise RuntimeError(
            "Strava token expired or unauthorized. "
            "Re-run scripts/tools/oauth_setup.py to get a new refresh token."
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


# ── OAuth helpers ─────────────────────────────────────────────────────────────

def exchange_code_for_tokens(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange a one-time OAuth authorisation code for a full token bundle.

    Called once after the user approves the Strava OAuth consent screen and
    Strava redirects back with ``?code=<value>`` in the URL.

    Args:
        code: The one-time code from the ``?code=`` query parameter.
        client_id: Strava app client ID.
        client_secret: Strava app client secret.

    Returns:
        Dict with access_token, refresh_token, expires_at, and athlete sub-dict.

    Raises:
        RuntimeError: If the exchange request fails.
    """
    logger.info("[strava] Exchanging OAuth code for tokens")
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Code exchange failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    if not data.get("access_token"):
        raise RuntimeError("No access_token in Strava code-exchange response.")
    return data


def get_athlete_info(access_token: str) -> dict:
    """Fetch basic profile information for the authenticated athlete.

    Args:
        access_token: Valid Strava access token.

    Returns:
        Dict with id, firstname, lastname, profile (photo URL).
        Returns an empty dict if the request fails.
    """
    resp = requests.get(
        f"{STRAVA_BASE}/athlete",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        logger.warning(f"[strava] get_athlete_info failed ({resp.status_code})")
        return {}
    data = resp.json()
    return {
        "id": data.get("id"),
        "firstname": data.get("firstname", ""),
        "lastname": data.get("lastname", ""),
        "profile": data.get("profile_medium") or data.get("profile", ""),
    }
