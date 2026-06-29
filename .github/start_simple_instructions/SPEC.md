# AI Endurance Coach — Build Specification

## Goal
Build an MVP that analyzes ONE Strava workout and produces a grounded,
natural-language coaching analysis with a recommendation. This is the demo
for an ETH Agentic Systems Lab Founder Track application.

## Modules to Build

### `src/strava.py`
- `get_recent_activities(limit=10)` → list of activity summaries
  (id, name, type, date, distance_km, moving_time_min, avg_hr, max_hr,
   avg_watts, start_latlng)
- `get_activity_detail(activity_id)` → full detail incl. `laps` list
  (lap number, distance, time, avg_watts, avg_hr, avg_speed)
- Read STRAVA_ACCESS_TOKEN from env. Raise clear error if token expired (401).

### `src/weather.py`
- `get_weather(lat, lon, date_iso)` → dict with avg_temp_c, max_temp_c,
  avg_humidity, avg_wind_kmh. Use Open-Meteo archive API (no key needed).
- Return None gracefully if data unavailable.

### `src/profile.py`
- `UserProfile` pydantic model: age, goal, experience, injuries, notes
- `.to_context()` → string for LLM context
- `DISCLAIMER` constant

### `src/skills.py`
Each skill is a function taking structured input and returning structured output.
- `analysis_skill(activity, profile)` → identifies workout structure (intervals?
  steady?), computes plan-vs-actual deviation if intervals detected, flags anomalies.
  Uses LLM to interpret laps. Returns dict: {structure, observations, deviations}.
- `weather_skill(activity)` → fetches weather via weather.py, uses LLM to assess
  likely performance impact. Returns dict: {conditions, likely_impact}.
- `question_skill(activity, analysis)` → generates 1-3 targeted clarifying questions
  for the user (sleep, stress, fueling, perceived effort). Returns list[str].
- `coaching_skill(activity, profile, analysis, weather, user_answers)` → synthesizes
  everything into final coaching text + next-step recommendation. MUST include
  disclaimer and stay grounded in provided data.

### `src/orchestrator.py`
- Build a LangGraph `StateGraph` with a TypedDict state holding:
  activity, profile, analysis, weather, questions, user_answers, final_output.
- Node order: analysis → weather → questions → (pause for user answers) → coaching.
- Expose two functions:
  - `run_analysis_phase(activity, profile)` → runs analysis+weather+questions,
    returns intermediate state + questions to ask user.
  - `run_coaching_phase(state, user_answers)` → runs coaching, returns final output.
- This two-phase design lets the UI pause to collect user answers (the agentic
  clarifying-question step).

### `app.py` (Streamlit)
- Sidebar: user profile questionnaire (age, goal, experience, injuries, notes).
- Main: button "Load my Strava activities" → dropdown to pick one.
- On selection: run analysis phase, display computed observations + weather.
- Show clarifying questions as text inputs.
- Button "Get my coaching analysis" → run coaching phase → display result.
- Show DISCLAIMER prominently.

## Prompts (define as constants)
- ANALYSIS_PROMPT: "You are an endurance coach analyzing workout laps. Identify
  whether this was intervals/steady/recovery. If intervals, infer the intended
  structure and compare to actual. Output observations grounded ONLY in given data."
- WEATHER_PROMPT: "Given workout data and weather, assess how conditions likely
  affected performance. Be specific (heat reduces power ~X%). Don't overstate."
- QUESTION_PROMPT: "Generate 1-3 short clarifying questions a coach would ask
  before giving advice (sleep, stress, fueling, RPE). Return as a list."
- COACHING_PROMPT: "Synthesize analysis + weather + user answers into supportive,
  specific coaching feedback and ONE concrete next-step recommendation. Stay
  grounded in data. End with the disclaimer."

## Acceptance Criteria
- [ ] Can load real Strava activities and pick one
- [ ] Correctly extracts laps/intervals
- [ ] Fetches weather for the activity's location & date
- [ ] Asks at least one clarifying question
- [ ] Produces grounded coaching text (no invented numbers)
- [ ] Always shows disclaimer
- [ ] Runs end-to-end in Streamlit and is deployable to Streamlit Cloud