"""Analyze pipeline request/response models."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from backend.models.profile import UserProfileRequest


class AnalyzeStartRequest(BaseModel):
    """Start Phase 1 of analysis: analysis + weather + questions."""

    activity_id: str
    profile: UserProfileRequest

    model_config = {"json_schema_extra": {"example": {
        "activity_id": "12345678",
        "profile": {"age": 28, "ftp": 280, "goal": "Build base", "experience": "Intermediate — training 3-4 times/week", "injuries": ""},
    }}}


class AnalysisResult(BaseModel):
    summary: list[str]
    structure: str
    observations: str
    deviations: str
    raw: str


class WeatherResult(BaseModel):
    conditions: str
    likely_impact: str


class AnalyzeStartResponse(BaseModel):
    """Response from Phase 1 — return to frontend, echo back in Phase 2."""

    activity_id: str
    analysis: AnalysisResult
    weather: WeatherResult
    questions: list[str]


class AnalyzeCoachRequest(BaseModel):
    """Phase 2: coaching synthesis."""

    activity_id: str
    profile: UserProfileRequest
    analysis: AnalysisResult
    weather: WeatherResult
    answers: dict[str, str] = {}

    model_config = {"json_schema_extra": {"example": {
        "activity_id": "12345678",
        "profile": {"age": 28, "ftp": 280, "goal": "Build base", "experience": "Intermediate — training 3-4 times/week", "injuries": ""},
        "analysis": {"summary": ["Threshold session"], "structure": "3x20min", "observations": "Good pacing", "deviations": "None", "raw": "..."},
        "weather": {"conditions": "20°C", "likely_impact": "Minimal"},
        "answers": {"How did you sleep?": "~7h, felt good"},
    }}}


class AnalyzeCoachResponse(BaseModel):
    coaching_output: str
