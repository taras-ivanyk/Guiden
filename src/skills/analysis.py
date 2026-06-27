"""Workout analysis skill — returns both a bullet summary and full details."""
from src.profile import UserProfile
from src.llm import chat
from src.skills.base import format_laps, parse_sections, health_block
from prompts.prompts import ANALYSIS_PROMPT
from src.logging_config import logger


def analysis_skill(activity: dict, profile: UserProfile) -> dict:
    """Analyse cycling workout structure and return summary + full details.

    Args:
        activity: Full activity dict including laps.
        profile: Athlete's UserProfile.

    Returns:
        Dict with keys: summary (list[str]), structure (str),
        observations (str), deviations (str), raw (str).
    """
    logger.info(f"[analysis_skill] Analysing: {activity.get('name')}")

    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}\n"
        f"Distance: {activity.get('distance_km')} km, "
        f"Duration: {activity.get('moving_time_min')} min\n"
        f"Avg HR: {activity.get('avg_hr')} bpm, Max HR: {activity.get('max_hr')} bpm\n"
        f"Avg Power: {activity.get('avg_watts') or 'N/A'} W\n"
        f"Elevation gain: {activity.get('total_elevation_gain') or 'N/A'} m\n\n"
        f"Laps:\n{format_laps(activity.get('laps', []))}\n\n"
        f"Athlete profile:\n{profile.to_context()}"
        + health_block(profile.injuries or "")
    )

    response = chat(ANALYSIS_PROMPT, user_msg, skill="analysis")

    summary_raw, structure, observations, deviations = parse_sections(
        response, ["SUMMARY", "STRUCTURE", "OBSERVATIONS", "DEVIATIONS"]
    )

    summary_bullets = [
        line.lstrip("-•* ").strip()
        for line in summary_raw.splitlines()
        if line.strip()
    ]

    return {
        "summary": summary_bullets,
        "structure": structure,
        "observations": observations,
        "deviations": deviations,
        "raw": response,
    }
