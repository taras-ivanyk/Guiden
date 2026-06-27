"""Coaching synthesis skill."""
from src.profile import UserProfile
from src.llm import chat
from src.skills.base import health_block
from prompts.prompts import COACHING_PROMPT
from src.logging_config import logger


def coaching_skill(
    activity: dict,
    profile: UserProfile,
    analysis: dict,
    weather: dict,
    user_answers: dict[str, str],
) -> str:
    """Synthesise all inputs into a final coaching analysis.

    Args:
        activity: Full activity detail dict.
        profile: Athlete's UserProfile.
        analysis: Output from analysis_skill.
        weather: Output from weather_skill.
        user_answers: Dict mapping question strings to athlete's answers.

    Returns:
        Final coaching text including disclaimer.
    """
    logger.info(f"[coaching_skill] Synthesising coaching for: {activity.get('name')}")

    answers_text = (
        "\n".join(f"Q: {q}\nA: {a}" for q, a in user_answers.items())
        if user_answers
        else "No answers provided."
    )

    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}, "
        f"Distance: {activity.get('distance_km')} km, "
        f"Duration: {activity.get('moving_time_min')} min\n"
        f"Avg HR: {activity.get('avg_hr')} bpm\n"
        f"Avg Power: {activity.get('avg_watts') or 'N/A'} W\n\n"
        f"Athlete profile:\n{profile.to_context()}\n\n"
        f"Workout analysis:\n{analysis.get('raw', '')}\n\n"
        f"Weather: {weather.get('conditions', 'N/A')}\n"
        f"Weather impact: {weather.get('likely_impact', 'N/A')}\n\n"
        f"Athlete answers:\n{answers_text}"
        + health_block(profile.injuries or "")
    )

    return chat(COACHING_PROMPT, user_msg, skill="coaching")
