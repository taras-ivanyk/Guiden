"""Analyze router — two-phase analysis pipeline."""
from __future__ import annotations

import requests
from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_valid_access_token
from backend.models.analyze import (
    AnalysisResult,
    AnalyzeCoachRequest,
    AnalyzeCoachResponse,
    AnalyzeStartRequest,
    AnalyzeStartResponse,
    WeatherResult,
)
from src.profile import UserProfile
from src.skills import analysis_skill, coaching_skill, question_skill, weather_skill
from src.logging_config import logger

router = APIRouter()

_STRAVA_BASE = "https://www.strava.com/api/v3"


def _fetch_activity(activity_id: str, access_token: str) -> dict:
    """Fetch activity detail from Strava using a raw access token."""
    resp = requests.get(
        f"{_STRAVA_BASE}/activities/{activity_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Strava token invalid.")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Strava error: {resp.text}")

    a = resp.json()
    laps = [
        {
            "lap_num": lap.get("lap_index", 0),
            "distance_km": round(lap.get("distance", 0) / 1000, 2),
            "time_min": round(lap.get("elapsed_time", 0) / 60, 1),
            "avg_watts": lap.get("average_watts"),
            "avg_hr": lap.get("average_heartrate"),
            "avg_speed_kmh": round(lap.get("average_speed", 0) * 3.6, 1),
        }
        for lap in a.get("laps", [])
    ]
    return {
        "id": str(a["id"]),
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


@router.post("/start", response_model=AnalyzeStartResponse)
def analyze_start(
    body: AnalyzeStartRequest,
    access_token: str = Depends(get_valid_access_token),
) -> AnalyzeStartResponse:
    """Phase 1: run analysis + weather + clarifying questions.

    Fetches the activity from Strava, runs the three agent skills, and
    returns intermediate results. The frontend stores these and echoes
    them back in the /coach call along with the user's answers.
    """
    logger.info(f"[api/analyze] start — activity_id={body.activity_id}")

    activity = _fetch_activity(body.activity_id, access_token)
    profile = UserProfile(
        age=body.profile.age,
        ftp=body.profile.ftp,
        goal=body.profile.goal,
        experience=body.profile.experience,
        injuries=body.profile.injuries,
    )

    try:
        analysis_raw = analysis_skill(activity, profile)
        weather_raw = weather_skill(activity)
        questions = question_skill(activity, analysis_raw, profile)
    except Exception as exc:
        logger.error(f"[api/analyze] skill error: {exc}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    return AnalyzeStartResponse(
        activity_id=body.activity_id,
        analysis=AnalysisResult(
            summary=analysis_raw.get("summary", []),
            structure=analysis_raw.get("structure", ""),
            observations=analysis_raw.get("observations", ""),
            deviations=analysis_raw.get("deviations", ""),
            raw=analysis_raw.get("raw", ""),
        ),
        weather=WeatherResult(
            conditions=weather_raw.get("conditions", ""),
            likely_impact=weather_raw.get("likely_impact", ""),
        ),
        questions=questions,
    )


@router.post("/coach", response_model=AnalyzeCoachResponse)
def analyze_coach(
    body: AnalyzeCoachRequest,
    access_token: str = Depends(get_valid_access_token),
) -> AnalyzeCoachResponse:
    """Phase 2: synthesize analysis + weather + answers into coaching feedback.

    The frontend echoes back the analysis/weather from Phase 1 to keep
    the backend stateless — no server-side storage needed.
    """
    logger.info(f"[api/analyze] coach — activity_id={body.activity_id}")

    activity = _fetch_activity(body.activity_id, access_token)
    profile = UserProfile(
        age=body.profile.age,
        ftp=body.profile.ftp,
        goal=body.profile.goal,
        experience=body.profile.experience,
        injuries=body.profile.injuries,
    )

    analysis_dict = {
        "summary": body.analysis.summary,
        "structure": body.analysis.structure,
        "observations": body.analysis.observations,
        "deviations": body.analysis.deviations,
        "raw": body.analysis.raw,
    }
    weather_dict = {
        "conditions": body.weather.conditions,
        "likely_impact": body.weather.likely_impact,
    }

    try:
        output = coaching_skill(
            activity=activity,
            profile=profile,
            analysis=analysis_dict,
            weather=weather_dict,
            user_answers=body.answers,
        )
    except Exception as exc:
        logger.error(f"[api/analyze] coaching error: {exc}")
        raise HTTPException(status_code=500, detail=f"Coaching synthesis failed: {exc}")

    return AnalyzeCoachResponse(coaching_output=output)
