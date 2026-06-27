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
    "You are an expert cycling coach analyzing a cyclist's workout laps. "
    "Identify whether this was intervals, threshold work, tempo, steady-state Z2, or recovery. "
    "If power data is available, reference it in context of FTP if known (e.g. % of FTP). "
    "Comment on cadence, power distribution, and pacing where data allows. "
    "Output observations grounded ONLY in the given data. "
    "If a metric is missing (e.g. no power meter), say so explicitly — do not invent numbers."
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

NEXT_SESSION_PROMPT = (
    "You are a data-driven cycling coach. Based on the athlete's recent training load "
    "and stated goal, recommend ONE specific next cycling session. "
    "Include: session type (e.g. threshold intervals, long Z2 ride), duration in minutes, "
    "target intensity (power zones or % FTP if known, HR zones otherwise), "
    "a brief warm-up/cool-down structure, and a short rationale. "
    "Be specific and actionable. Stay grounded in the provided data. "
    f"Always end with this disclaimer:\n\n{DISCLAIMER}"
)

TRAINING_PLAN_PROMPT = (
    "You are an expert cycling coach. Create a detailed multi-week cycling training plan. "
    "Apply these principles: progressive overload (increase load gradually week-over-week), "
    "a recovery week every 3-4 weeks (reduce volume ~30-40%), "
    "polarized intensity (~80% Z1-Z2, ~20% Z4-Z5), "
    "and strictly respect the athlete's available training time. "
    "Return ONLY a valid JSON array — no markdown fences, no extra text. "
    "Each element is one week with this exact structure: "
    '{"week_num": 1, "focus": "Base endurance", "total_hours": 6.0, '
    '"sessions": [{"day": "Monday", "type": "Recovery ride", '
    '"duration_min": 45, "intensity": "Zone 1-2"}], '
    '"recovery_days": ["Thursday", "Sunday"]}. '
    "Use full day names (Monday, Tuesday, etc.). "
    "All sessions must be cycling-specific. Never invent metrics not provided."
)

RACE_PREP_PROMPT = (
    "You are an expert cycling coach preparing an athlete for a target event. "
    "Create a HIGH-LEVEL race preparation plan organized into phases: "
    "1) Base (aerobic foundation), 2) Build (intensity and specificity), "
    "3) Peak (race-specific sharpening), 4) Taper (fatigue reduction). "
    "For each phase provide: phase name, duration in weeks, key training focus, "
    "and 2-3 example session types per week. "
    "Keep it strategic and concise — this is an overview, not a day-by-day schedule. "
    "The athlete can ask follow-up questions to expand any phase. "
    "Stay cycling-specific (power zones, FTP percentages, interval types). "
    f"Always end with this disclaimer:\n\n{DISCLAIMER}"
)

RACE_EXPAND_PROMPT = (
    "You are an expert cycling coach. The athlete has a high-level race preparation plan "
    "and is asking for more detail on a specific section. "
    "Expand ONLY the section relevant to their question — provide specific workouts, "
    "durations, intensity targets (power zones / % FTP), recovery guidance, and rationale. "
    "Keep the rest of the plan at a high level. "
    "Stay grounded in what the athlete told you. Do not invent metrics. "
    f"Always end with this disclaimer:\n\n{DISCLAIMER}"
)


def _llm() -> ChatOpenAI:
    """Return a configured ChatOpenAI instance.

    Reads OPENAI_BASE_URL from env to support custom/proxy endpoints.
    """
    model = os.getenv("OPENAI_MODEL", "openai.eu.gpt-4.1-mini-2025-04-14")
    base_url = os.getenv("OPENAI_BASE_URL")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.4"))
    kwargs = {"model": model, "temperature": temperature}
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


# ---------------------------------------------------------------------------
# Training plan & race prep skills
# ---------------------------------------------------------------------------

def next_session_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
) -> str:
    """Recommend ONE specific next cycling session.

    Args:
        profile: Athlete's UserProfile.
        plan_inputs: Dict with goal, experience, hours_per_day, etc.
        recent_summary: Recent training aggregate from get_recent_summary.

    Returns:
        Text description of the recommended next session.
    """
    user_msg = _build_plan_context(profile, plan_inputs, recent_summary)
    user_msg += "\n\nRecommend ONE specific next cycling session for this athlete."
    return _chat(NEXT_SESSION_PROMPT, user_msg)


def training_plan_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
) -> "list[dict] | str":
    """Generate a structured multi-week cycling training plan.

    Args:
        profile: Athlete's UserProfile.
        plan_inputs: Dict with keys: days_per_week (int), hours_per_day (float),
            goal (str), experience (str), sleep_hours (float), injuries (str),
            weeks (int).
        recent_summary: Recent training aggregate from get_recent_summary.

    Returns:
        Parsed list of weekly plan dicts if JSON is valid, else raw text string.
    """
    user_msg = _build_plan_context(profile, plan_inputs, recent_summary)
    user_msg += (
        f"\n\nGenerate a {plan_inputs.get('weeks', 4)}-week cycling training plan "
        "as a JSON array following the specified structure. Return ONLY the JSON array."
    )
    response = _chat(TRAINING_PLAN_PROMPT, user_msg)
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
    return response


def race_prep_skill(profile: UserProfile, race_inputs: dict) -> str:
    """Generate a high-level cycling race preparation plan.

    Args:
        profile: Athlete's UserProfile.
        race_inputs: Dict with keys: race_type (str), race_date (str),
            distance_km (float), elevation_m (int), weekly_hours (float),
            goal (str), current_fitness (str).

    Returns:
        High-level phased race prep plan as text.
    """
    weeks_out = _weeks_until(race_inputs.get("race_date", ""))
    user_msg = (
        f"Athlete profile:\n{profile.to_context()}\n\n"
        f"Race type: {race_inputs.get('race_type')}\n"
        f"Race date: {race_inputs.get('race_date')} ({weeks_out} weeks away)\n"
        f"Distance: {race_inputs.get('distance_km')} km, "
        f"Elevation: {race_inputs.get('elevation_m')} m\n"
        f"Available weekly training hours: {race_inputs.get('weekly_hours')}\n"
        f"Current fitness: {race_inputs.get('current_fitness')}\n"
        f"Goal: {race_inputs.get('goal')}\n\n"
        "Generate a high-level race preparation plan."
    )
    return _chat(RACE_PREP_PROMPT, user_msg)


def expand_race_section_skill(current_plan: str, user_question: str) -> str:
    """Expand a specific section of a race prep plan based on athlete follow-up.

    Args:
        current_plan: The existing high-level race prep plan text.
        user_question: The athlete's follow-up question or expansion request.

    Returns:
        Expanded section text with detail added to the relevant phase.
    """
    user_msg = (
        f"Current plan:\n{current_plan}\n\n"
        f"Athlete question: {user_question}\n\n"
        "Expand the relevant section in detail."
    )
    return _chat(RACE_EXPAND_PROMPT, user_msg)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_plan_context(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
) -> str:
    """Build a formatted user message string for training plan skills.

    Args:
        profile: Athlete's UserProfile.
        plan_inputs: Training plan input parameters from the UI form.
        recent_summary: Recent training aggregate stats.

    Returns:
        Formatted multi-line string ready for an LLM prompt.
    """
    lines = [
        f"Athlete profile:\n{profile.to_context()}",
        f"Goal: {plan_inputs.get('goal', 'Not specified')}",
        f"Current fitness / experience: {plan_inputs.get('experience', 'Not specified')}",
        f"Training days per week: {plan_inputs.get('days_per_week', 4)}",
        f"Hours available per training day: {plan_inputs.get('hours_per_day', 1.5)}",
        f"Plan length: {plan_inputs.get('weeks', 4)} weeks",
        f"Average sleep: {plan_inputs.get('sleep_hours', 7.5)} hours/night",
    ]
    if plan_inputs.get("injuries"):
        lines.append(f"Injuries / limitations: {plan_inputs['injuries']}")
    if recent_summary and recent_summary.get("num_rides", 0) > 0:
        lines.append(
            f"\nRecent {recent_summary.get('days', 14)}-day training summary: "
            f"{recent_summary['num_rides']} rides, "
            f"{recent_summary['total_hours']} hours, "
            f"{recent_summary['total_distance_km']} km, "
            f"avg power: {recent_summary.get('avg_power') or 'N/A'} W, "
            f"{recent_summary['num_hard_sessions']} hard sessions."
        )
    return "\n".join(lines)


def _weeks_until(race_date_str: str) -> int:
    """Calculate whole weeks from today until a race date.

    Args:
        race_date_str: ISO date string (YYYY-MM-DD).

    Returns:
        Number of whole weeks remaining, or 0 if date is invalid or past.
    """
    if not race_date_str:
        return 0
    try:
        from datetime import date
        race = date.fromisoformat(race_date_str)
        delta = (race - date.today()).days
        return max(0, delta // 7)
    except ValueError:
        return 0
