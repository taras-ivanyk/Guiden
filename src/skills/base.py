"""Shared helpers and health-condition logic used across all skills."""
from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.profile import UserProfile

# ── Health condition detection ────────────────────────────────────────────────
_SERIOUS_KEYWORDS = frozenset({
    "heart", "cardiac", "aorta", "chest pain", "arrhythmia", "pacemaker",
    "bypass", "angina", "cardiomyopathy", "stenosis", "atrial fibrillation",
    "a-fib", "afib", "coronary",
})


def has_serious_condition(injuries: str) -> bool:
    """Return True if the injuries string mentions a serious cardiovascular keyword."""
    lower = injuries.lower()
    return any(kw in lower for kw in _SERIOUS_KEYWORDS)


def safety_warning(injuries: str) -> str:
    """Return a prominent safety warning string for serious conditions.

    Returns empty string if no serious condition is detected.
    """
    if not injuries or not has_serious_condition(injuries):
        return ""
    return (
        "⚠️ **SAFETY NOTICE:** Based on your reported health condition "
        f"(*{injuries}*), this plan has been adapted to prioritise safety. "
        "**Please consult a cardiologist or physician before beginning any "
        "new training program.** Avoid Zone 4–5 efforts until medically cleared."
    )


def health_block(injuries: str) -> str:
    """Build a safety instruction block to inject into LLM user messages.

    Returns an empty string if no health conditions are reported.
    """
    if not injuries or injuries.strip() in ("", "None", "none"):
        return ""
    serious = has_serious_condition(injuries)
    base = (
        f'\n\nCRITICAL — HEALTH CONDITIONS REPORTED: "{injuries}". '
        "You MUST adapt ALL recommendations for safety. "
    )
    if serious:
        return (
            base
            + "The condition appears cardiovascular/serious. "
            "Be VERY conservative: do NOT prescribe Zone 4–5 intensity. "
            "Recommend obtaining medical/cardiologist clearance before following this plan. "
            "Explicitly state in the output how the plan accounts for this condition."
        )
    return base + "Explicitly reference how every recommendation adapts for this condition."


# ── Lap formatting ────────────────────────────────────────────────────────────

def format_laps(laps: list[dict]) -> str:
    """Format laps list as a readable string for LLM context."""
    if not laps:
        return "No lap data available."
    rows = []
    for lap in laps:
        rows.append(
            f"  Lap {lap.get('lap_num', '?')}: "
            f"{lap.get('distance_km')} km in {lap.get('time_min')} min | "
            f"HR: {lap.get('avg_hr') or 'N/A'} bpm | "
            f"Power: {lap.get('avg_watts') or 'N/A'} W | "
            f"Speed: {lap.get('avg_speed_kmh')} km/h"
        )
    return "\n".join(rows)


# ── Section parser ────────────────────────────────────────────────────────────

def parse_sections(text: str, section_names: list[str]) -> list[str]:
    """Extract named sections from LLM output text."""
    results: list[str] = []
    upper = text.upper()
    for i, name in enumerate(section_names):
        key = name.upper()
        start = upper.find(key)
        if start == -1:
            results.append("")
            continue
        end = len(text)
        for j in range(i + 1, len(section_names)):
            nk = section_names[j].upper()
            np = upper.find(nk, start + len(key))
            if np != -1:
                end = np
                break
        results.append(text[start + len(key):end].strip().lstrip(":").strip())
    return results


# ── Plan context builder ──────────────────────────────────────────────────────

def build_plan_context(
    profile: "UserProfile",
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> str:
    """Build a formatted user message for training plan and next-session skills."""
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
    if availability:
        avail_lines: list[str] = []
        for day, val in availability.items():
            if not val:
                continue
            # New format: {"start": "HH:MM", "end": "HH:MM"}
            if isinstance(val, dict):
                avail_lines.append(
                    f"  {day}: {val.get('start', '?')} – {val.get('end', '?')}"
                )
            else:
                # Legacy list format (e.g. ["Morning", "Evening"])
                avail_lines.append(f"  {day}: {', '.join(val)}")
        if avail_lines:
            lines.append(
                "Weekly training windows (AUTHORITATIVE — schedule sessions "
                "only on these days, within these exact time slots):\n"
                + "\n".join(avail_lines)
            )
    if recent_summary and recent_summary.get("num_rides", 0) > 0:
        lines.append(
            f"\nRecent {recent_summary.get('days', 14)}-day training summary: "
            f"{recent_summary['num_rides']} rides, "
            f"{recent_summary['total_hours']} h, "
            f"{recent_summary['total_distance_km']} km, "
            f"avg power: {recent_summary.get('avg_power') or 'N/A'} W, "
            f"{recent_summary['num_hard_sessions']} hard sessions."
        )
    # Always append health block
    lines.append(health_block(plan_inputs.get("injuries", "")))
    return "\n".join(lines)


# ── Date helper ───────────────────────────────────────────────────────────────

def weeks_until(race_date_str: str) -> int:
    """Return whole weeks from today until a race date (0 if past or invalid)."""
    if not race_date_str:
        return 0
    try:
        race = _date.fromisoformat(race_date_str)
        delta = (race - _date.today()).days
        return max(0, delta // 7)
    except ValueError:
        return 0
