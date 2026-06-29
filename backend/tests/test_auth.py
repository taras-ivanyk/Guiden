"""Tests for auth endpoints."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_strava_url_missing_client_id() -> None:
    """Should return 503 when STRAVA_CLIENT_ID is not configured."""
    with patch("backend.routers.auth.STRAVA_CLIENT_ID", ""):
        resp = client.get("/api/auth/strava/url")
    assert resp.status_code == 503


def test_strava_url_returns_url() -> None:
    with patch("backend.routers.auth.STRAVA_CLIENT_ID", "test_id"):
        resp = client.get("/api/auth/strava/url")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "strava.com" in data["url"]
    assert "test_id" in data["url"]


def test_strava_callback_invalid_code() -> None:
    """Should return 400 when Strava rejects the code."""
    with (
        patch("backend.routers.auth.STRAVA_CLIENT_ID", "test_id"),
        patch("backend.routers.auth.STRAVA_CLIENT_SECRET", "test_secret"),
        patch(
            "backend.routers.auth.exchange_code_for_tokens",
            side_effect=RuntimeError("invalid code"),
        ),
    ):
        resp = client.post("/api/auth/strava/callback", json={"code": "bad_code"})
    assert resp.status_code == 400
    assert "invalid code" in resp.json()["detail"]


def test_strava_callback_success() -> None:
    fake_tokens = {
        "access_token": "acc_abc",
        "refresh_token": "ref_xyz",
        "expires_at": 9999999999,
    }
    fake_athlete = {"id": 1, "firstname": "Taras", "lastname": "I", "profile": ""}

    with (
        patch("backend.routers.auth.STRAVA_CLIENT_ID", "test_id"),
        patch("backend.routers.auth.STRAVA_CLIENT_SECRET", "test_secret"),
        patch("backend.routers.auth.exchange_code_for_tokens", return_value=fake_tokens),
        patch("backend.routers.auth.get_athlete_info", return_value=fake_athlete),
        patch("backend.middleware.auth._secret", return_value="test_secret_key_32chars_padding"),
    ):
        resp = client.post("/api/auth/strava/callback", json={"code": "good_code"})

    assert resp.status_code == 200
    data = resp.json()
    assert "jwt" in data
    assert data["athlete"]["firstname"] == "Taras"
