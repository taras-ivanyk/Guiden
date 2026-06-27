"""Multi-week training plan skill."""
from __future__ import annotations

import json

from src.profile import UserProfile
from src.llm import chat
from src.skills.base import build_plan_context
from prompts.prompts import TRAINING_PLAN_PROMPT
from src.logging_config import logger


def training_plan_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> list[dict] | str:
    """Generate a structured multi-week cycling training plan.

    Args:
        profile: Athlete's UserProfile.
        plan_inputs: Dict with days_per_week, hours_per_day, goal, experience,
            sleep_hours, injuries, weeks.
        recent_summary: Recent training aggregate from get_recent_summary.
        availability: Optional weekly availability dict.

    Returns:
        Parsed list of weekly plan dicts if JSON is valid, else raw text string.
    """
    weeks = plan_inputs.get("weeks", 4)
    logger.info(f"[training_plan_skill] Generating {weeks}-week plan")

    user_msg = build_plan_context(profile, plan_inputs, recent_summary, availability)
    user_msg += (
        f"\n\nGenerate a {weeks}-week cycling training plan "
        "as a JSON array following the specified structure. Return ONLY the JSON array."
    )

    response = chat(TRAINING_PLAN_PROMPT, user_msg, skill="training_plan")

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        plan = json.loads(cleaned)
        if isinstance(plan, list):
            return plan
    except (json.JSONDecodeError, ValueError):
        pass

    logger.warning("[training_plan_skill] JSON parse failed — returning raw text")
    return response
