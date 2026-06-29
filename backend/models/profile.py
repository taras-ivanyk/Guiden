"""Athlete profile request model."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class UserProfileRequest(BaseModel):
    """Athlete profile sent from the frontend."""

    age: Optional[int] = Field(None, ge=10, le=100, description="Athlete age")
    ftp: Optional[int] = Field(None, ge=0, le=600, description="FTP in watts (0 = unknown)")
    goal: str = Field("", description="Primary training goal")
    experience: str = Field("", description="Experience / fitness level label")
    injuries: str = Field("", description="Injuries or health conditions")

    model_config = {"json_schema_extra": {"example": {
        "age": 28,
        "ftp": 280,
        "goal": "Improve FTP by 20W",
        "experience": "Intermediate — training 3-4 times/week",
        "injuries": "",
    }}}
