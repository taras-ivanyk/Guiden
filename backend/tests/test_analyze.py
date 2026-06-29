"""Tests for analyze endpoints."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.middleware.auth import create_jwt

client = TestClient(app)

_FAKE_SECRET = "test_secret_key_32chars_paddingXX"

_FAKE_TOKENS = {
    "access_token": "acc_test",
    "refresh_token": "ref_test",
    "expires_at": 9999999999,
}
_FAKE_ATHLETE = {"id": 1, "firstname": "Taras", "lastname": "I"}


def _make_jwt() -> str:
    with patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET):
        return create_jwt(_FAKE_TOKENS, _FAKE_ATHLETE)


_PROFILE = {
    "age": 28, "ftp": 280,
    "goal": "Improve FTP",
    "experience": "Intermediate — training 3-4 times/week",
    "injuries": "",
}

_FAKE_ACTIVITY = {
    "id": "123", "name": "Test ride", "type": "Ride", "date": "2026-06-25",
    "distance_km": 62.4, "moving_time_min": 138.0,
    "avg_hr": 152, "max_hr": 178, "avg_watts": 218,
    "start_latlng": [47.37, 8.54], "total_elevation_gain": 640,
    "description": "", "laps": [],
}

_FAKE_ANALYSIS = {
    "summary": ["Threshold session detected"],
    "structure": "3x20 min threshold",
    "observations": "Power fade on rep 3",
    "deviations": "None",
    "raw": "SUMMARY: ...",
}

_FAKE_WEATHER = {
    "conditions": "20°C avg",
    "likely_impact": "Minimal performance impact.",
    "raw_data": None,
}


def test_analyze_start_unauthorized() -> None:
    resp = client.post("/api/analyze/start", json={"activity_id": "1", "profile": _PROFILE})
    assert resp.status_code == 401


def test_analyze_start_success() -> None:
    jwt = _make_jwt()

    with (
        patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET),
        patch("backend.routers.analyze._fetch_activity", return_value=_FAKE_ACTIVITY),
        patch("backend.routers.analyze.analysis_skill", return_value=_FAKE_ANALYSIS),
        patch("backend.routers.analyze.weather_skill", return_value=_FAKE_WEATHER),
        patch("backend.routers.analyze.question_skill", return_value=["How did you sleep?"]),
        patch("backend.deps.get_valid_access_token", return_value="acc_test"),
    ):
        resp = client.post(
            "/api/analyze/start",
            json={"activity_id": "123", "profile": _PROFILE},
            headers={"Authorization": f"Bearer {jwt}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["activity_id"] == "123"
    assert len(data["questions"]) == 1
    assert data["analysis"]["structure"] == "3x20 min threshold"


def test_analyze_coach_success() -> None:
    jwt = _make_jwt()

    with (
        patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET),
        patch("backend.routers.analyze._fetch_activity", return_value=_FAKE_ACTIVITY),
        patch("backend.routers.analyze.coaching_skill", return_value="Great session! **Next step:** ..."),
        patch("backend.deps.get_valid_access_token", return_value="acc_test"),
    ):
        resp = client.post(
            "/api/analyze/coach",
            json={
                "activity_id": "123",
                "profile": _PROFILE,
                "analysis": {**_FAKE_ANALYSIS},
                "weather": _FAKE_WEATHER,
                "answers": {"How did you sleep?": "7h, felt good"},
            },
            headers={"Authorization": f"Bearer {jwt}"},
        )

    assert resp.status_code == 200
    assert "coaching_output" in resp.json()
