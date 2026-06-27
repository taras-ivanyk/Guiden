# 🚴 AI Cycling Coach

**Your data-driven personal cycling coach — powered by Strava & OpenAI**

---

## The Problem
Most cyclists train without knowing *why* a session went well or badly. Was it the heat? Accumulated fatigue? Poor pacing? Without a coach, that context is lost.

## The Solution
An agentic AI coach that orchestrates multiple specialised skills — analysis, weather assessment, clarifying questions, and coaching synthesis — to explain exactly what happened in your ride and what to do next. Grounded in your real Strava data, never hallucinated.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Analyze Workout** | Deep-dive into any Strava ride: power zones, weather impact, pacing, lap analysis, and a concrete next-step recommendation |
| 📅 **Training Plan** | Personalized multi-week plan with progressive overload, recovery weeks, and clickable day-level session detail |
| 🏁 **Race Prep** *(beta)* | Phased race preparation (Base → Build → Peak → Taper) with chat-based section expansion |
| 📅 **Training Calendar** | Set your weekly availability by day and time slot — the plan schedules around you |
| 🔢 **Token Tracking** | Live token/cost counter per session, configurable budget |

---

## Live Demo

> Local / self-hosted: `http://localhost:8501`  
> Streamlit Cloud: *coming soon*

---

## Tech Stack

- **Python 3.11+**
- `streamlit` — web UI
- `openai` / `langchain-openai` — LLM calls (gpt-4o-mini by default)
- `langgraph` — agent orchestration
- `requests` — Strava API & Open-Meteo weather API
- `pydantic` — data models
- `python-dotenv` — configuration

---

## Setup & Run

### Prerequisites
- Python 3.11+
- OpenAI API key
- Strava account + API app (free to create at [strava.com/settings/api](https://www.strava.com/settings/api))

### 1. Clone and create environment
```bash
git clone <repo-url>
cd ai-cycling-coach
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 3. Get your Strava credentials

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api) and create an app
2. Note your **Client ID** and **Client Secret**
3. Run the OAuth helper to get a refresh token:
```bash
python3 scripts/tools/oauth_setup.py
```
4. Paste the printed `STRAVA_REFRESH_TOKEN` into your `.env`

> **Note:** Strava access tokens expire every 6 hours — the app automatically refreshes them using your `STRAVA_REFRESH_TOKEN` (which doesn't expire).

### 4. Run
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Configuration

All settings are read from `.env` with safe defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required. Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model to use |
| `OPENAI_BASE_URL` | — | Custom/proxy endpoint (leave blank for OpenAI default) |
| `LLM_TEMPERATURE` | `0.4` | LLM creativity/randomness |
| `MAX_OUTPUT_TOKENS` | `1500` | Max tokens per LLM response |
| `SESSION_TOKEN_BUDGET` | `50000` | Max tokens per session before blocking |
| `COST_PER_M_INPUT` | `0.15` | Cost per 1M input tokens (USD) |
| `COST_PER_M_OUTPUT` | `0.60` | Cost per 1M output tokens (USD) |
| `STRAVA_CLIENT_ID` | — | Required. Your Strava app client ID |
| `STRAVA_CLIENT_SECRET` | — | Required. Your Strava app client secret |
| `STRAVA_REFRESH_TOKEN` | — | Required. Get via `scripts/tools/oauth_setup.py` |
| `TOP_K_ACTIVITIES` | `10` | How many recent activities to fetch by default |
| `DEFAULT_WEEKS_AHEAD` | `4` | Default training plan length in weeks |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |

---

## Architecture

```
Strava API ──────► activity data (laps, power, HR, GPS)
                        │
User profile ───────────┤  (age, FTP, goal, injuries, notes)
                        │
Open-Meteo ─────────────┤  (historical weather by GPS + date)
                        │
Weekly Calendar ─────────┤  (available days + time slots)
                        ▼
            LangGraph Orchestrator
            ├─ analysis_skill     (workout type, deviations, summary)
            ├─ weather_skill      (conditions + performance impact)
            ├─ question_skill     (1-3 clarifying questions)
            ├─ coaching_skill     (final synthesis + recommendation)
            ├─ next_session_skill (next ride recommendation)
            ├─ training_plan_skill (multi-week JSON plan)
            ├─ expand_session_skill (on-demand day detail — lazy)
            └─ race_prep_skill   (phased race preparation)
                        │
            Natural-language coaching output
```

---

## Project Structure

```
app.py                    # thin entry: routing between pages
requirements.txt
src/
  config.py               # all env vars + defaults
  logging_config.py       # logging setup
  llm.py                  # central OpenAI wrapper (logs tokens/cost)
  strava.py               # Strava API (incl. paginated date-range fetch)
  weather.py              # Open-Meteo
  profile.py              # UserProfile model + disclaimer
  orchestrator.py         # routes to skill flows
  skills/
    __init__.py
    base.py               # shared helpers + health condition detection
    analysis.py
    weather_skill.py
    questions.py
    coaching.py
    next_session.py
    training_plan.py
    expand_session.py     # on-demand day detail
    race_prep.py
ui/
  components.py           # CSS, sidebar, token counter
  home.py                 # landing page
  analyze.py              # workout analysis page
  plan.py                 # training plan page
  race.py                 # race prep page
  calendar.py             # weekly availability grid
prompts/
  prompts.py              # all *_PROMPT constants
scripts/
  tools/
    oauth_setup.py        # one-time Strava OAuth helper
    test_strava.py        # Strava connectivity test
```

---

## Roadmap

- [ ] Multi-sport support (running, swimming)
- [ ] Training reminders / calendar notifications
- [ ] Mobile-optimised layout
- [ ] Garmin / Wahoo / Polar integrations
- [ ] Segment analysis (KOM attempts, climb performance)
- [ ] Long-term fitness tracking (CTL/ATL/TSB)

---

## Disclaimer

> ⚠️ This tool is AI-generated and for **informational purposes only**. It is **NOT medical advice**. Always consult a qualified coach or healthcare professional — especially if you have any health conditions — before making changes to your training.

---

*Built for the ETH Agentic Systems Lab — AI Founder Track application.*
