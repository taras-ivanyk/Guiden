"""Race preparation and section-expansion skills."""
from src.profile import UserProfile
from src.llm import chat
from src.skills.base import health_block, weeks_until
from prompts.prompts import RACE_PREP_PROMPT, RACE_EXPAND_PROMPT
from src.logging_config import logger


def race_prep_skill(profile: UserProfile, race_inputs: dict) -> str:
    """Generate a high-level cycling race preparation plan.

    Args:
        profile: Athlete's UserProfile.
        race_inputs: Dict with race_type, race_date, distance_km,
            elevation_m, weekly_hours, goal, current_fitness.

    Returns:
        High-level phased race prep plan as text.
    """
    logger.info(f"[race_prep_skill] Generating plan for: {race_inputs.get('race_type')}")
    weeks_out = weeks_until(race_inputs.get("race_date", ""))
    user_msg = (
        f"Athlete profile:\n{profile.to_context()}\n\n"
        f"Race type: {race_inputs.get('race_type')}\n"
        f"Race date: {race_inputs.get('race_date')} ({weeks_out} weeks away)\n"
        f"Distance: {race_inputs.get('distance_km')} km, "
        f"Elevation: {race_inputs.get('elevation_m')} m\n"
        f"Available weekly training hours: {race_inputs.get('weekly_hours')}\n"
        f"Current fitness: {race_inputs.get('current_fitness')}\n"
        f"Goal: {race_inputs.get('goal')}"
        + health_block(profile.injuries or "")
    )
    return chat(RACE_PREP_PROMPT, user_msg, skill="race_prep")


def expand_race_section_skill(current_plan: str, user_question: str) -> str:
    """Expand a specific section of a race prep plan based on athlete follow-up.

    Args:
        current_plan: The existing high-level race prep plan text.
        user_question: The athlete's follow-up question or expansion request.

    Returns:
        Expanded section text.
    """
    logger.info("[expand_race_section_skill] Expanding race prep section")
    user_msg = (
        f"Current plan:\n{current_plan}\n\n"
        f"Athlete question: {user_question}\n\nExpand the relevant section in detail."
    )
    return chat(RACE_EXPAND_PROMPT, user_msg, skill="race_expand")
