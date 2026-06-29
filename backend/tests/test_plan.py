"""Tests for plan endpoints."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.middleware.auth import create_jwt

client = TestClient(app)

_FAKE_SECRET = "test_secret_key_32chars_paddingXX"
_FAKE_TOKENS = {"access_token": "acc", "refresh_token": "ref", "expires_at": 9999999999}
_FAKE_ATHLETE = {"id": 1, "firstname": "T", "lastname": "I"}


def _jwt() -> str:
    with patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET):
        return create_jwt(_FAKE_TOKENS, _FAKE_ATHLETE)


_PLAN_BODY = {
    "profile": {"age": 28, "ftp": 280, "goal": "FTP", "experience": "Intermediate — training 3-4 times/week", "injuries": ""},
    "calendar": [{"day": "Tuesday", "start": "07:00", "end": "09:00", "duration_min": 120}],
    "goal": "Improve FTP",
    "experience": "Intermediate — training 3-4 times/week",
    "sleep_hours": 7.5,
    "injuries": "",
    "weeks": 2,
}

_FAKE_PLAN = [
    {
        "week_num": 1, "focus": "Base", "total_hours": 2.0,
        "sessions": [{"day": "Tuesday", "type": "Z2 ride", "duration_min": 90, "intensity": "Z1-2", "start_time": "07:00"}],
        "recovery_days": ["Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    }
]


def test_next_session_success() -> None:
    with (
        patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET),
        patch("backend.deps.get_valid_access_token", return_value="acc"),
        patch("backend.routers.plan.next_session_skill", return_value="TYPE: Z2 ride | DAY: Tuesday | ..."),
    ):
        resp = client.post(
            "/api/plan/next-session",
            json=_PLAN_BODY,
            headers={"Authorization": f"Bearer {_jwt()}"},
        )
    assert resp.status_code == 200
    assert "next_session" in resp.json()


def test_multi_week_plan_success() -> None:
    with (
        patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET),
        patch("backend.deps.get_valid_access_token", return_value="acc"),
        patch("backend.routers.plan.training_plan_skill", return_value=_FAKE_PLAN),
    ):
        resp = client.post(
            "/api/plan/multi-week",
            json=_PLAN_BODY,
            headers={"Authorization": f"Bearer {_jwt()}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["plan"]) == 1
    assert data["plan"][0]["week_num"] == 1
    assert data["plan"][0]["sessions"][0]["day"] == "Tuesday"


def test_multi_week_plan_no_calendar() -> None:
    """Calendar is required — should return 422 if empty."""
    body = {**_PLAN_BODY, "calendar": []}
    with (
        patch("backend.middleware.auth._secret", return_value=_FAKE_SECRET),
        patch("backend.deps.get_valid_access_token", return_value="acc"),
    ):
        resp = client.post(
            "/api/plan/multi-week",
            json=body,
            headers={"Authorization": f"Bearer {_jwt()}"},
        )
    assert resp.status_code == 422
