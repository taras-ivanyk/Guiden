"""Mock activity and recent training summary for demo mode."""
from __future__ import annotations

import json
from pathlib import Path

_MOCK_DIR = Path(__file__).parent


def get_mock_activity() -> dict:
    """Return a realistic fake Strava activity for demo mode.

    Session: 3x20 min threshold intervals, Zurich, 2026-06-25.
    Real GPS coordinates so the weather skill fires against Open-Meteo.

    Returns:
        Activity dict matching the schema returned by strava.get_activity_detail.
    """
    with open(_MOCK_DIR / "activity.json", encoding="utf-8") as fh:
        return json.load(fh)


def get_mock_recent_summary() -> dict:
    """Return a realistic recent 14-day training summary for demo mode.

    Returns:
        Dict with keys: days, num_rides, total_hours, total_distance_km,
        avg_power, num_hard_sessions.
    """
    return {
        "days": 14,
        "num_rides": 9,
        "total_hours": 13.5,
        "total_distance_km": 468.0,
        "avg_power": 207,
        "num_hard_sessions": 3,
    }
