"""Next session recommendation skill."""
from __future__ import annotations

from src.profile import UserProfile
from src.llm import chat
from src.skills.base import build_plan_context
from prompts.prompts import NEXT_SESSION_PROMPT
from src.logging_config import logger


def next_session_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> str:
    """Recommend ONE specific next cycling session.

    Args:
        profile: Athlete's UserProfile.
        plan_inputs: Dict with goal, experience, hours_per_day, etc.
        recent_summary: Recent training aggregate from get_recent_summary.
        availability: Optional weekly availability dict.

    Returns:
        Text description of the recommended next session.
    """
    logger.info("[next_session_skill] Generating next session recommendation")
    user_msg = build_plan_context(profile, plan_inputs, recent_summary, availability)
    user_msg += "\n\nRecommend ONE specific next cycling session for this athlete."
    return chat(NEXT_SESSION_PROMPT, user_msg, skill="next_session")
