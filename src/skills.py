"""LLM-based coaching skills for the AI Endurance Coach."""

import json
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.weather import get_weather
from src.profile import UserProfile, DISCLAIMER


# ---------------------------------------------------------------------------
# Prompt constants
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = (
    "You are an endurance coach analyzing workout laps. "
    "Identify whether this was intervals, steady-state, or recovery. "
    "If intervals, infer the intended structure and compare to actual performance. "
    "Output observations grounded ONLY in the given data. "
    "If a metric is missing (e.g. no power data), say so explicitly — do not invent numbers."
)

WEATHER_PROMPT = (
    "You are an endurance sports coach. Given the workout summary and weather conditions, "
    "assess how the conditions likely affected performance. Be specific where possible "
    "(e.g. heat above 25°C typically reduces sustainable power by 5-8%). "
    "Do not overstate certainty. If weather data is unavailable, say so."
)

QUESTION_PROMPT = (
    "You are an endurance coach preparing to give feedback. "
    "Generate 1 to 3 short, targeted clarifying questions you would ask the athlete "
    "before giving advice. Focus on factors not visible in the data: sleep quality, "
    "stress levels, fueling/hydration, or perceived effort (RPE). "
    "Return ONLY a JSON array of question strings, e.g. [\"Question 1\", \"Question 2\"]."
)

COACHING_PROMPT = (
    "You are a supportive, data-grounded endurance coach. "
    "Synthesize the workout analysis, weather impact, and athlete's answers "
    "into specific, actionable coaching feedback. "
    "End with ONE concrete next-step recommendation. "
    "Stay grounded in the provided data — never invent metrics. "
    f"Always end your response with this exact disclaimer on a new line:\n\n{DISCLAIMER}"
)


def _llm() -> ChatOpenAI:
    """Return a configured ChatOpenAI instance.

    Reads OPENAI_BASE_URL from env to support custom/proxy endpoints.
    """
    model = os.getenv("OPENAI_MODEL", "openai.eu.gpt-4.1-mini-2025-04-14")
    base_url = os.getenv("OPENAI_BASE_URL")
    kwargs = {"model": model, "temperature": 0.3}
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def _chat(system: str, user: str) -> str:
    """Run a simple system+user LLM call and return the text response.

    Args:
        system: System prompt text.
        user: User message text.

    Returns:
        Model response as a string.
    """
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    response = _llm().invoke(messages)
    return response.content.strip()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def analysis_skill(activity: dict, profile: UserProfile) -> dict:
    """Analyze workout structure and identify deviations.

    Args:
        activity: Full activity detail dict (including `laps`).
        profile: Athlete's UserProfile.

    Returns:
        Dict with keys: structure (str), observations (str), deviations (str).
    """
    laps_text = _format_laps(activity.get("laps", []))
    profile_text = profile.to_context()

    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}\n"
        f"Distance: {activity.get('distance_km')} km, "
        f"Duration: {activity.get('moving_time_min')} min\n"
        f"Avg HR: {activity.get('avg_hr')} bpm, Max HR: {activity.get('max_hr')} bpm\n"
        f"Avg Power: {activity.get('avg_watts') or 'N/A'} W\n\n"
        f"Laps:\n{laps_text}\n\n"
        f"Athlete profile:\n{profile_text}\n\n"
        "Analyze the workout structure and any notable observations or deviations. "
        "Format your response with three sections: STRUCTURE, OBSERVATIONS, DEVIATIONS."
    )

    response = _chat(ANALYSIS_PROMPT, user_msg)

    structure, observations, deviations = _parse_sections(
        response, ["STRUCTURE", "OBSERVATIONS", "DEVIATIONS"]
    )

    return {
        "structure": structure,
        "observations": observations,
        "deviations": deviations,
        "raw": response,
    }


def weather_skill(activity: dict) -> dict:
    """Fetch weather for the activity and assess its performance impact.

    Args:
        activity: Activity dict with `start_latlng` and `date` fields.

    Returns:
        Dict with keys: conditions (str), likely_impact (str).
    """
    latlng = activity.get("start_latlng")
    date = activity.get("date")

    weather_data: Optional[dict] = None
    if latlng and len(latlng) == 2 and date:
        weather_data = get_weather(latlng[0], latlng[1], date)

    if weather_data:
        conditions_text = (
            f"Temperature: {weather_data.get('avg_temp_c')}°C avg / "
            f"{weather_data.get('max_temp_c')}°C max\n"
            f"Humidity: {weather_data.get('avg_humidity')}%\n"
            f"Wind: {weather_data.get('avg_wind_kmh')} km/h"
        )
    else:
        conditions_text = "Weather data unavailable for this activity location/date."

    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}, "
        f"Duration: {activity.get('moving_time_min')} min\n\n"
        f"Weather conditions:\n{conditions_text}\n\n"
        "Assess likely impact on performance."
    )

    response = _chat(WEATHER_PROMPT, user_msg)

    return {
        "conditions": conditions_text,
        "likely_impact": response,
        "raw_data": weather_data,
    }


def question_skill(activity: dict, analysis: dict) -> list[str]:
    """Generate 1-3 targeted clarifying questions for the athlete.

    Args:
        activity: Activity summary dict.
        analysis: Output from analysis_skill.

    Returns:
        List of question strings (1-3 questions).
    """
    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}\n\n"
        f"Workout analysis:\n{analysis.get('raw', '')}\n\n"
        "What clarifying questions would you ask the athlete?"
    )

    response = _chat(QUESTION_PROMPT, user_msg)

    try:
        # Strip markdown code fences if present
        cleaned = response.strip().strip("```json").strip("```").strip()
        questions = json.loads(cleaned)
        if isinstance(questions, list):
            return [str(q) for q in questions[:3]]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: return raw lines as questions
    lines = [l.strip().lstrip("-•*123456789. ") for l in response.splitlines() if l.strip()]
    return lines[:3] if lines else ["How did this workout feel overall (1–10)?"]


def coaching_skill(
    activity: dict,
    profile: UserProfile,
    analysis: dict,
    weather: dict,
    user_answers: dict[str, str],
) -> str:
    """Synthesize all inputs into a final coaching analysis.

    Args:
        activity: Full activity detail dict.
        profile: Athlete's UserProfile.
        analysis: Output from analysis_skill.
        weather: Output from weather_skill.
        user_answers: Dict mapping question strings to athlete's answers.

    Returns:
        Final coaching text string (includes disclaimer).
    """
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
        f"Weather conditions:\n{weather.get('conditions', 'N/A')}\n"
        f"Weather impact:\n{weather.get('likely_impact', 'N/A')}\n\n"
        f"Athlete's answers:\n{answers_text}\n\n"
        "Provide your coaching analysis and one concrete next-step recommendation."
    )

    return _chat(COACHING_PROMPT, user_msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_laps(laps: list[dict]) -> str:
    """Format laps list as a readable string for LLM context."""
    if not laps:
        return "No lap data available."
    rows = []
    for lap in laps:
        row = (
            f"  Lap {lap.get('lap_num', '?')}: "
            f"{lap.get('distance_km')} km in {lap.get('time_min')} min | "
            f"HR: {lap.get('avg_hr') or 'N/A'} bpm | "
            f"Power: {lap.get('avg_watts') or 'N/A'} W | "
            f"Speed: {lap.get('avg_speed_kmh')} km/h"
        )
        rows.append(row)
    return "\n".join(rows)


def _parse_sections(text: str, section_names: list[str]) -> list[str]:
    """Extract named sections from LLM output.

    Args:
        text: Full LLM response text.
        section_names: Ordered list of section header names to extract.

    Returns:
        List of section content strings (same order as section_names).
        Empty string for any section not found.
    """
    results = []
    upper = text.upper()
    for i, name in enumerate(section_names):
        start_key = name.upper()
        start = upper.find(start_key)
        if start == -1:
            results.append("")
            continue
        # Find end (next section or end of text)
        end = len(text)
        for j in range(i + 1, len(section_names)):
            next_key = section_names[j].upper()
            next_pos = upper.find(next_key, start + len(start_key))
            if next_pos != -1:
                end = next_pos
                break
        content = text[start + len(start_key):end].strip().lstrip(":").strip()
        results.append(content)
    return results
