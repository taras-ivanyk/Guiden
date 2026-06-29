# App Overview — Guiden

## What it does

Guiden is an **agentic coaching system** that connects to your Strava account, pulls real workout data, and produces grounded coaching analysis, training plans, and race preparation — without hallucinating numbers.

The key word is **agentic**: instead of sending everything to one big prompt, the system orchestrates a pipeline of specialised skills that each do one thing well, can be tested independently, and produce output explicitly grounded in real data.

---

## The three modes

| Mode | What happens |
|------|-------------|
| **Analyze Workout** | Pick any Strava ride → 4-agent pipeline (analysis → weather → clarifying questions → coaching synthesis) → natural-language coaching feedback |
| **Training Plan** | Fill in availability + goals → multi-week structured plan (JSON) with on-demand per-day expansion |
| **Race Prep** | Target event details → phased plan (Base → Build → Peak → Taper) → chat-based section expansion |

---

## Why multiple skills, not one prompt

A single prompt approach fails for cycling coaching because:

1. **Weather requires a real API call** — you can't know the conditions without fetching them from Open-Meteo
2. **Clarifying questions require a pause** — the system must stop, show questions to the user, collect answers, then continue
3. **Each skill can be tuned independently** — the analysis agent uses different instructions, temperature, and output format than the coaching agent
4. **Grounding is verifiable** — each skill's output is visible in the UI before the final synthesis, so the user can see exactly what went into the coaching advice

The orchestrator (LangGraph) wires the analysis skills into two phases that allow the UI to pause between them:

```
Phase 1 — runs immediately after user picks an activity:
  activity + profile
      ├─► analysis_skill   → workout type, 3-5 summary bullets, full details
      ├─► weather_skill    → conditions text + performance impact assessment
      └─► question_skill   → 1–3 clarifying questions for the athlete
                   │
        [Streamlit pauses — user reads analysis, answers questions]
                   │
Phase 2 — runs after user submits answers:
  coaching_skill(analysis + weather + user_answers) → final coaching text + disclaimer
```

For training plans and race prep the orchestrator calls skills sequentially without LangGraph — keeping it simple where the pause mechanic isn't needed.

---

## Data flow

```
Browser
    │
    ▼
app.py  (page router ~50 lines)
    │
    ├── ui/analyze.py ──► src/strava.py ──► Strava REST API
    │       │                   │
    │       │         activity + laps returned
    │       │
    │       └──► src/orchestrator.py
    │                   │
    │         ┌─────────┼──────────┐
    │         ▼         ▼          ▼
    │   analysis_   weather_   question_
    │   skill       skill      skill
    │                 │
    │           Open-Meteo Archive API
    │
    │         [user answers questions in UI]
    │                 │
    │           coaching_skill ──► final output in st.chat_message
    │
    ├── ui/plan.py ──► orchestrator.run_training_plan()
    │       │               ├── next_session_skill  → text
    │       │               └── training_plan_skill → JSON list[dict]
    │       │
    │       └── expand_session_skill  (lazy — only on user click)
    │
    └── ui/race.py ──► orchestrator.run_race_prep()
                            ├── race_prep_skill        → text
                            └── expand_race_section_skill  (on st.chat_input)
```

---

## Health & safety system

Every skill that produces recommendations injects a safety instruction block via `health_block(injuries)` from `src/skills/base.py`.

### How detection works (keyword matching)

```python
_SERIOUS_KEYWORDS = {
    "heart", "cardiac", "aorta", "chest pain", "arrhythmia",
    "pacemaker", "bypass", "angina", "cardiomyopathy",
    "coronary", "a-fib", "afib", "stenosis",
}
```

### Two levels of response

| Condition type | LLM instruction | UI behaviour |
|---------------|-----------------|--------------|
| Any injury/condition | Adapt all recommendations; explicitly reference the condition in output | No banner unless serious |
| Cardiovascular keyword matched | No Zone 4–5; recommend cardiologist clearance; explicitly adapt | `st.warning()` banner shown before any output |

The final coaching/plan output **must visibly state** how the condition was accounted for — the prompt enforces this explicitly.

---

## Token management

All LLM calls route through `src/llm.py` which wraps LangChain's `ChatOpenAI`:

| Step | What happens |
|------|-------------|
| Pre-call | Check `st.session_state["_session_tokens"]` against `SESSION_TOKEN_BUDGET` |
| If over budget | Return a human-readable error string; no API call made |
| Post-call | Extract `prompt_tokens` + `completion_tokens` from response metadata |
| Cost calc | `(prompt / 1M × COST_PER_M_INPUT) + (completion / 1M × COST_PER_M_OUTPUT)` |
| Persist | Accumulate totals in `st.session_state` |
| Sidebar | `ui/components.py` renders a live counter once ≥1 call is made |

**Token-saving design decisions:**
- Analysis summary bullets shown by default; full STRUCTURE/OBSERVATIONS/DEVIATIONS sections hidden in an expander
- `expand_session_skill` is **lazy** — only called when user clicks "Details", never proactively
- Expanded sessions are cached in `st.session_state[f"expanded_{week}_{day}"]` so re-clicks are free
- Strava data sent to each skill is trimmed to only the fields that skill uses

---

## Logging

Configured in `src/logging_config.py`. Level controlled by `LOG_LEVEL` env var (default `INFO`).

**Format:** `HH:MM:SS [LEVEL] cycling_coach: [skill_name] message`

**What is logged:**

| Event | Level | Example |
|-------|-------|---------|
| LLM call initiated | INFO | `[analysis] LLM call — model=gpt-4o-mini, temp=0.4` |
| LLM response | INFO | `[analysis] tokens — prompt=312, completion=487, total=799, cost=$0.00041` |
| Strava API call | INFO | `[strava] get_activities_in_range — start=2025-08-25, after_epoch=1756080000` |
| Strava 401 | ERROR | `[strava] 401 — token expired` |
| Open-Meteo call | INFO | `[weather_skill] Open-Meteo API → lat=47.3, lon=8.5, date=2025-08-25` |
| Budget exceeded | WARNING | `[analysis] Session budget exceeded (50123/50000 tokens)` |
| JSON parse failure | WARNING | `[training_plan_skill] JSON parse failed — returning raw text` |

---

## Configuration reference

All settings in `src/config.py`, read from `.env` with safe defaults. Full list in `.env.example`.

| Variable | Default | Effect |
|----------|---------|--------|
| `OPENAI_MODEL` | `gpt-4o-mini` | Which model all skills use |
| `LLM_TEMPERATURE` | `0.4` | Lower = more deterministic coaching |
| `MAX_OUTPUT_TOKENS` | `1500` | Per-response cap (enforced by LangChain) |
| `SESSION_TOKEN_BUDGET` | `50000` | ~$0.015 per full session at gpt-4o-mini rates |
| `COST_PER_M_INPUT` | `0.15` | Update if you switch models |
| `COST_PER_M_OUTPUT` | `0.60` | Update if you switch models |
| `TOP_K_ACTIVITIES` | `10` | Used by `get_recent_activities()` only |
| `LOG_LEVEL` | `INFO` | Set to `DEBUG` to log full prompts |

---

## Full project structure

```
app.py                        ← page router (~50 lines)
requirements.txt
.env.example
README.md

src/
  config.py                   ← all env vars with safe defaults
  logging_config.py           ← logging setup, exports `logger`
  llm.py                      ← central chat() + token tracking
  strava.py                   ← Strava API (recent / range / detail / summary)
  weather.py                  ← Open-Meteo historical weather
  profile.py                  ← UserProfile (Pydantic model) + DISCLAIMER
  orchestrator.py             ← LangGraph graphs + public run_* functions
  skills/
    __init__.py               ← re-exports all 9 public skill functions
    base.py                   ← health detection + shared formatting helpers
    analysis.py               ← workout structure analysis (summary + details)
    weather_skill.py          ← weather fetch + performance impact assessment
    questions.py              ← clarifying questions generation
    coaching.py               ← final synthesis skill
    next_session.py           ← single-session recommendation
    training_plan.py          ← multi-week JSON plan generation
    expand_session.py         ← lazy per-day full detail (on-demand only)
    race_prep.py              ← race phases + section expansion

ui/
  components.py               ← CSS injection, sidebar, token counter, disclaimer
  home.py                     ← landing page with feature cards
  analyze.py                  ← analyze-workout page
  plan.py                     ← training plan page + calendar integration
  race.py                     ← race prep page + chat expansion
  calendar.py                 ← weekly availability grid component

prompts/
  __init__.py
  prompts.py                  ← all *_PROMPT string constants (single source of truth)

scripts/tools/
  oauth_setup.py              ← one-time Strava OAuth token bootstrap
  test_strava.py              ← Strava connectivity smoke test

docs/
  overview.md                 ← this file
  skills.md                   ← per-skill reference
```

---

## Adding a new skill — checklist

1. Create `src/skills/my_skill.py` with a single public function
2. Export it from `src/skills/__init__.py`
3. Add the prompt constant to `prompts/prompts.py`
4. Call `chat(MY_PROMPT, user_msg, skill="my_skill")` — logging and token tracking happen automatically
5. Inject `health_block(profile.injuries or "")` into the user message if the skill produces training recommendations
6. Add a public entry point in `src/orchestrator.py` if the UI needs it
7. Call from the relevant `ui/` page module
8. Document in `docs/skills.md`
