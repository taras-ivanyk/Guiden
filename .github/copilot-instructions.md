# Copilot Instructions — AI Endurance Coach

## Project Overview
This is an **agentic AI endurance-sports coaching MVP** for an application to the
ETH Agentic Systems Lab (AI Founder Track). It analyzes a user's Strava workout
data using an orchestration of LLM agents ("skills") and produces a natural-language
coaching analysis explaining WHY a workout went the way it did (e.g. weather impact,
fatigue, pacing) and what to do next.

The MVP scope is intentionally narrow: **only the "Workout Analysis" feature.**
Other features (training plans, race prep) are roadmap-only — do NOT build them.

## Tech Stack (use exactly these)
- Python 3.11+
- `openai` (model: `gpt-4o-mini` for cost; configurable via env)
- `langgraph` + `langchain-openai` for agent orchestration
- `streamlit` for the web UI/demo
- `requests` for Strava + Open-Meteo APIs
- `pydantic` for data models
- `python-dotenv` for config

## Architecture
Strava API ──> activity data (laps, power, HR, GPS, time)
│
User profile ───────┤  (age, goal, injuries, notes — from questionnaire)
│
Open-Meteo ─────────┤  (historical weather by GPS + date)
▼
LangGraph Orchestrator
├─ analysis_skill   (computes plan vs actual, deviations)
├─ weather_skill    (fetches & interprets weather impact)
├─ question_skill   (asks user clarifying Qs: sleep/stress)
└─ coaching_skill   (synthesizes everything into advice)
▼
Natural-language coaching analysis + recommendation

## Coding Conventions
- All source code lives in `src/`. UI entry point is `app.py` at root.
- Use type hints everywhere. Add docstrings to every function.
- Keep functions small and single-purpose.
- Never hardcode secrets — always read from environment via `python-dotenv`.
- All LLM prompts should be defined as module-level string constants named `*_PROMPT`.
- Use `gpt-4o-mini` by default; read model name from `os.getenv("OPENAI_MODEL", "gpt-4o-mini")`.
- Handle API errors gracefully (Strava tokens expire every 6h — surface a clear message).

## Critical Domain Rules
- This is NOT medical advice. Every coaching output MUST include a short disclaimer.
- When data is missing (e.g. no power meter), the agent must say so, not hallucinate numbers.
- The coaching agent must GROUND its analysis in the actual data + weather, never invent metrics.
- If the agent is uncertain, it should ASK the user a clarifying question rather than guess.

## What Makes This "Agentic" (important for the demo)
- The system orchestrates multiple specialized skills, not a single prompt.
- It actively asks clarifying questions (sleep, stress, nutrition) before concluding.
- It calls real tools (Strava API, weather API) and reasons over the results.

## Out of Scope (do NOT implement)
- Training plan generation, race preparation planning (roadmap only)
- User database / auth beyond a simple session profile
- Multi-user support
- Payment / monetization