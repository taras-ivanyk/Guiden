# Skills Reference — Guiden

All skills live in `src/skills/`. Each is a single Python file with one primary public function. Every skill routes its LLM call through `src/llm.chat()` for automatic token logging, cost tracking, and budget enforcement.

---

## Table of contents

1. [base.py — Shared helpers](#1-basepy--shared-helpers)
2. [analysis.py — Workout analysis](#2-analysispy--workout-analysis)
3. [weather_skill.py — Weather impact](#3-weather_skillpy--weather-impact)
4. [questions.py — Clarifying questions](#4-questionspy--clarifying-questions)
5. [coaching.py — Coaching synthesis](#5-coachingpy--coaching-synthesis)
6. [next_session.py — Next session recommendation](#6-next_sessionpy--next-session-recommendation)
7. [training_plan.py — Multi-week training plan](#7-training_planpy--multi-week-training-plan)
8. [expand_session.py — On-demand session detail](#8-expand_sessionpy--on-demand-session-detail)
9. [race_prep.py — Race preparation](#9-race_preppy--race-preparation)

---

## 1. `base.py` — Shared helpers

Not a skill itself — a utility module imported by every skill.

### Health condition detection

```python
has_serious_condition(injuries: str) -> bool
```
Returns `True` if `injuries` contains any keyword from the cardiovascular keyword set:
`heart, cardiac, aorta, chest pain, arrhythmia, pacemaker, bypass, angina, cardiomyopathy, coronary, a-fib, afib, stenosis`

```python
safety_warning(injuries: str) -> str
```
Returns a `⚠️ SAFETY NOTICE` markdown string for use with `st.warning()`. Returns `""` if no serious condition detected.

```python
health_block(injuries: str) -> str
```
Builds the CRITICAL instruction block injected into every LLM user message that involves training recommendations. Two levels:
- **Any condition** → "Adapt ALL recommendations; explicitly reference this condition in output"
- **Cardiovascular keyword** → additionally: no Zone 4–5, recommend cardiologist clearance

### Data formatting

```python
format_laps(laps: list[dict]) -> str
```
Converts the Strava laps list into a human-readable multi-line string for LLM context. Each line includes lap number, distance, time, average HR, average power, and speed.

```python
parse_sections(text: str, section_names: list[str]) -> list[str]
```
Extracts named sections from LLM output by scanning for uppercase section headers (e.g. `SUMMARY:`, `STRUCTURE:`). Returns one content string per requested section.

### Plan context builder

```python
build_plan_context(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> str
```
Assembles the complete user message for training plan and next-session skills. Includes: athlete profile, goal, experience, training days/week, hours/day, sleep, injuries, weekly availability grid, and recent 14-day training summary. Always appends `health_block(injuries)` at the end.

### Date helper

```python
weeks_until(race_date_str: str) -> int
```
Returns whole weeks from today to a race date string (ISO format). Returns `0` for past dates or invalid strings.

---

## 2. `analysis.py` — Workout analysis

**Role in pipeline:** Phase 1 — runs immediately after user picks an activity.

```python
analysis_skill(activity: dict, profile: UserProfile) -> dict
```

### What it does
Sends the full activity context (name, date, type, distance, time, HR, power, elevation, laps) plus athlete profile to the LLM. Asks the model to identify the session type and produce structured observations.

### Inputs
| Field | Source |
|-------|--------|
| `activity` | `strava.get_activity_detail()` — includes full laps list |
| `profile` | Sidebar UserProfile — `injuries` used for `health_block` injection |

### Output dict
| Key | Type | Description |
|-----|------|-------------|
| `summary` | `list[str]` | 3–5 concise bullet points (shown by default in UI) |
| `structure` | `str` | Session type and intended structure |
| `observations` | `str` | Notable patterns in power, HR, pacing |
| `deviations` | `str` | Anything unexpected or concerning |
| `raw` | `str` | Full LLM response (passed to downstream skills) |

### Prompt strategy (`ANALYSIS_PROMPT`)
- Instructs the LLM to identify: intervals / threshold / tempo / steady Z2 / recovery
- References FTP if available (`profile.ftp`)
- Requests four explicit sections: `SUMMARY`, `STRUCTURE`, `OBSERVATIONS`, `DEVIATIONS`
- `parse_sections()` extracts each into its own key
- Summary bullets are split from the SUMMARY section by line

### Health integration
`health_block(profile.injuries)` appended to user message — analysis output may note how conditions affect interpretation.

### Token notes
Laps are pre-formatted by `format_laps()` — only relevant fields sent, not full JSON.

---

## 3. `weather_skill.py` — Weather impact

**Role in pipeline:** Phase 1 — runs in parallel with analysis (same LangGraph phase).

```python
weather_skill(activity: dict) -> dict
```

### What it does
1. Extracts `start_latlng` and `date` from the activity
2. Calls `get_weather(lat, lon, date)` — Open-Meteo Archive API (no API key needed)
3. Formats the conditions into a text summary
4. Asks the LLM to assess how those conditions likely affected cycling performance

### Inputs
| Field | Source |
|-------|--------|
| `activity["start_latlng"]` | Strava — `[lat, lon]` of activity start |
| `activity["date"]` | Strava — `start_date_local[:10]` |

### Output dict
| Key | Type | Description |
|-----|------|-------------|
| `conditions` | `str` | Formatted weather text (temp avg/max, humidity, wind) |
| `likely_impact` | `str` | LLM assessment of performance impact |
| `raw_data` | `dict\|None` | Raw Open-Meteo response dict (or `None` if unavailable) |

### Prompt strategy (`WEATHER_PROMPT`)
- Instructs the LLM to be specific: e.g. "heat above 25°C typically reduces sustainable power by 5–8%"
- Must not overstate certainty
- If weather data is unavailable, the conditions text says so — the LLM is instructed to acknowledge this

### Token notes
Does not inject health block (weather impact is not health-dependent).

---

## 4. `questions.py` — Clarifying questions

**Role in pipeline:** Phase 1 — runs after analysis, before coaching.

```python
question_skill(
    activity: dict,
    analysis: dict,
    profile: Optional[UserProfile] = None,
) -> list[str]
```

### What it does
Generates 1–3 short clarifying questions about factors not visible in Strava data: sleep quality, stress levels, fueling/hydration, perceived effort (RPE). The Streamlit UI shows these to the user before running the coaching skill.

### Inputs
| Field | Source |
|-------|--------|
| `activity` | Activity summary (name, date, type) |
| `analysis["raw"]` | Full text from `analysis_skill` — context for question generation |
| `profile.injuries` | Used to tailor questions (e.g. not asking about high-intensity if cardiac condition) |

### Output
`list[str]` — 1 to 3 question strings. Falls back to `["How did this workout feel overall (1–10)?"]` if the LLM response cannot be parsed.

### Prompt strategy (`QUESTION_PROMPT`)
- Instructs the LLM to return `ONLY a JSON array of strings`
- Response is JSON-parsed; falls back to line splitting if that fails

### Health integration
`health_block(profile.injuries)` injected so questions can be tailored (e.g. asking about chest discomfort if cardiac condition present).

---

## 5. `coaching.py` — Coaching synthesis

**Role in pipeline:** Phase 2 — runs after user submits answers to clarifying questions.

```python
coaching_skill(
    activity: dict,
    profile: UserProfile,
    analysis: dict,
    weather: dict,
    user_answers: dict[str, str],
) -> str
```

### What it does
Synthesises all prior outputs — workout analysis, weather impact, and the athlete's own answers — into a single, actionable coaching response. Always ends with `DISCLAIMER`.

### Inputs
| Field | Source |
|-------|--------|
| `activity` | Full detail dict |
| `profile` | Sidebar profile — FTP, injuries, goal, experience |
| `analysis["raw"]` | Full analysis text from Phase 1 |
| `weather["conditions"]`, `weather["likely_impact"]` | From `weather_skill` |
| `user_answers` | Dict mapping question → answer from UI |

### Output
`str` — full coaching text with disclaimer. Rendered in `st.chat_message("assistant")`.

### Prompt strategy (`COACHING_PROMPT`)
- Instructs LLM to synthesise all inputs into specific, actionable feedback
- Must end with ONE concrete next-step recommendation
- Explicitly forbidden from inventing metrics not present in the data
- Health block enforces safety adaptations in the coaching text

---

## 6. `next_session.py` — Next session recommendation

**Role in pipeline:** Training Plan mode — always generated (even when `next_only=True`).

```python
next_session_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> str
```

### What it does
Recommends ONE specific next cycling session based on the athlete's recent load, stated goal, and available time.

### Inputs (via `build_plan_context`)
| Field | Description |
|-------|-------------|
| `profile` | Age, FTP, goal, injuries |
| `plan_inputs["goal"]` | Athlete's stated goal (free text) |
| `plan_inputs["experience"]` | Mapped fitness label |
| `plan_inputs["days_per_week"]` | How many days/week to train |
| `plan_inputs["hours_per_day"]` | Hours available per session |
| `plan_inputs["sleep_hours"]` | Average sleep (recovery proxy) |
| `recent_summary` | 14-day aggregate: rides, hours, avg power, hard sessions |
| `availability` | Weekly grid: `{"Monday": ["Morning"], ...}` |

### Output
`str` — session recommendation including type, duration, target zones (power or HR), warm-up/cool-down structure, rationale, and disclaimer.

### Prompt strategy (`NEXT_SESSION_PROMPT`)
- Requests specific, actionable recommendation (not generic advice)
- Uses power zones or % FTP if FTP is known; HR zones otherwise

---

## 7. `training_plan.py` — Multi-week training plan

**Role in pipeline:** Training Plan mode — generated when user clicks "Generate Multi-Week Plan".

```python
training_plan_skill(
    profile: UserProfile,
    plan_inputs: dict,
    recent_summary: dict,
    availability: dict | None = None,
) -> list[dict] | str
```

### What it does
Generates a structured multi-week cycling training plan. Tries to return parsed JSON; falls back to raw text if JSON parsing fails.

### Training principles applied (via prompt)
- Progressive overload (load increases week-over-week)
- Recovery week every 3–4 weeks (volume reduced ~30–40%)
- Polarised intensity (~80% Z1–Z2, ~20% Z4–Z5)
- Respects `days_per_week`, `hours_per_day`, and weekly availability

### Output format (when JSON is valid)
```python
[
    {
        "week_num": 1,
        "focus": "Base endurance",
        "total_hours": 6.0,
        "sessions": [
            {
                "day": "Monday",
                "type": "Recovery ride",
                "duration_min": 45,
                "intensity": "Zone 1-2"
            },
            ...
        ],
        "recovery_days": ["Thursday", "Sunday"]
    },
    ...
]
```

### UI rendering
- One `st.expander` per week (Week 1 expanded by default)
- Each session row has a "Details" button → triggers `expand_session_skill` (lazy)
- Parsed JSON renders as structured cards; raw text fallback renders in `st.chat_message`

### Prompt strategy (`TRAINING_PLAN_PROMPT`)
- Instructs LLM to return ONLY a JSON array (no markdown, no preamble)
- Code strips markdown fences if the LLM wraps the JSON anyway
- Falls back gracefully to raw text on any parse failure

---

## 8. `expand_session.py` — On-demand session detail

**Role in pipeline:** Training Plan mode — lazy, only called when user clicks "Details" on a session.

```python
expand_session_skill(
    week_num: int,
    day: str,
    session: dict,
    profile: UserProfile,
) -> str
```

### What it does
Generates a **complete, detailed breakdown** of one training session. This is intentionally lazy to save tokens — it is never called proactively. The result is cached in `st.session_state[f"expanded_{week_num}_{day}"]` so clicking the same session a second time is free.

### Inputs
| Field | Description |
|-------|-------------|
| `week_num` | Week number in the plan (for context) |
| `day` | Day of week (e.g. "Monday") |
| `session["type"]` | Session type from the plan |
| `session["duration_min"]` | Target duration |
| `session["intensity"]` | Target intensity zone |
| `profile` | Athlete profile — FTP, injuries for health block |

### Output
`str` — full session instructions including:
1. Warm-up (duration, cadence target, effort zone)
2. Main set (interval structure, target watts/% FTP, recoveries)
3. Cool-down (duration, effort)
4. Target RPE (1–10)
5. Fueling note (before/during/after)
6. How the athlete's health conditions are accounted for

### Prompt strategy (`EXPAND_SESSION_PROMPT`)
- Structured output with six explicit numbered sections
- Health block ensures cardiovascular conditions are respected
- Explicitly told to be specific enough to follow exactly

### Token cost
Medium — only called on explicit user action. With gpt-4o-mini and `MAX_OUTPUT_TOKENS=1500`, typically ~600–900 tokens per session expansion.

---

## 9. `race_prep.py` — Race preparation

**Role in pipeline:** Race Prep mode — two functions, one for initial plan, one for follow-up expansion.

### Initial plan

```python
race_prep_skill(profile: UserProfile, race_inputs: dict) -> str
```

Generates a high-level phased race preparation plan.

### Inputs
| Key | Description |
|-----|-------------|
| `race_inputs["race_type"]` | "Road race" or "Time trial" |
| `race_inputs["race_date"]` | ISO date string |
| `race_inputs["distance_km"]` | Expected race distance |
| `race_inputs["elevation_m"]` | Expected elevation gain |
| `race_inputs["weekly_hours"]` | Available training hours per week |
| `race_inputs["goal"]` | Athlete's goal (free text) |
| `race_inputs["current_fitness"]` | Mapped fitness label |

`weeks_until(race_date)` is called to compute time-to-race and inject it into context.

### Output
`str` — high-level phased plan in Markdown. Structure:
- **Base phase** — aerobic foundation (weeks + focus + 2–3 session types/week)
- **Build phase** — intensity and specificity
- **Peak phase** — race-specific sharpening
- **Taper phase** — fatigue reduction before race

### Prompt strategy (`RACE_PREP_PROMPT`)
- Emphasises this is a **strategic overview**, not a day-by-day schedule
- Tells athlete they can ask follow-up questions to expand any phase
- Health block ensures cardiovascular adaptations are explicit

---

### Section expansion

```python
expand_race_section_skill(current_plan: str, user_question: str) -> str
```

Expands one specific section of the race prep plan in response to a follow-up question.

### How it works
The full current plan text is included in the user message alongside the question. The LLM is instructed to expand ONLY the relevant section and keep the rest at high level. Called from the `st.chat_input` at the bottom of the race prep page.

**Example questions that trigger expansion:**
- "Expand the build phase"
- "What should my taper week look like exactly?"
- "Give me specific workouts for the peak phase"

### Token notes
Medium-high — passes the full plan as context each time. With a 4-week plan this is typically 500–800 tokens input.

---

## Skills dependency map

```
analysis_skill ──────────────────────┐
weather_skill  ──────────────────────┤──► coaching_skill → final output
question_skill ──► [user answers] ───┘

next_session_skill  ──────────────────► text recommendation
training_plan_skill ──────────────────► list[dict] plan
  └── expand_session_skill (lazy) ─────► per-day detail

race_prep_skill ──────────────────────► phased plan text
  └── expand_race_section_skill ────────► expanded section text
```

All skills share:
- `src/llm.chat()` — LLM calls, token logging, budget enforcement
- `src/skills/base.health_block()` — health safety injection (except weather_skill)
- `prompts/prompts.py` — prompt constants
- `src/logging_config.logger` — structured logging
