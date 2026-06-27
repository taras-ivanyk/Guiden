"""Clarifying questions skill."""
import json
from typing import Optional

from src.profile import UserProfile
from src.llm import chat
from src.skills.base import health_block
from prompts.prompts import QUESTION_PROMPT
from src.logging_config import logger


def question_skill(
    activity: dict,
    analysis: dict,
    profile: Optional[UserProfile] = None,
) -> list[str]:
    """Generate 1–3 targeted clarifying questions for the athlete.

    Args:
        activity: Activity summary dict.
        analysis: Output from analysis_skill.
        profile: Athlete profile — used to tailor questions to health conditions.

    Returns:
        List of 1–3 question strings.
    """
    logger.info(f"[question_skill] Generating questions for: {activity.get('name')}")

    injuries = (profile.injuries or "") if profile else ""
    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}\n\n"
        f"Workout analysis:\n{analysis.get('raw', '')}"
        + health_block(injuries)
    )

    response = chat(QUESTION_PROMPT, user_msg, skill="questions")

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        questions = json.loads(cleaned)
        if isinstance(questions, list):
            return [str(q) for q in questions[:3]]
    except (json.JSONDecodeError, ValueError):
        pass

    lines = [ln.strip().lstrip("-•*123456789. ") for ln in response.splitlines() if ln.strip()]
    return lines[:3] if lines else ["How did this workout feel overall (1–10)?"]
