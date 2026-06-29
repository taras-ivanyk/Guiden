# App Overview — Guiden

## What it does

Guiden is an **agentic coaching system** that connects to your Strava account, pulls real workout data, and produces grounded coaching analysis and training plans — without hallucinating numbers.

The system orchestrates a pipeline of specialised skills that each do one thing well, can be tested independently, and produce output grounded in real data.

---

## Architecture

```
Browser (React :5173)
       │
       │ Vite proxy /api/* → localhost:8000
       ▼
FastAPI (:8000)
       │
       ├─ /api/auth/strava/url      → generates Strava OAuth URL
       ├─ /api/auth/strava/callback → exchanges code for JWT
       │
       ├─ /api/strava/activities    → fetches rides from Strava API
       ├─ /api/strava/recent-summary
       │
       ├─ /api/analyze/start   ─────┐
       └─ /api/analyze/coach  ──────┤
                                    ▼
                              src/skills/
                              ├── analysis_skill
                              ├── weather_skill   → Open-Meteo API
                              ├── question_skill
                              └── coaching_skill
                                        │
                                        ▼
                                  prompts/prompts.py
                                  (single source of truth for all prompts)
```

---

## Analyze Workout — two-phase pipeline

```
Phase 1 — /api/analyze/start:
  activity_id + profile
      ├─► analysis_skill   → workout summary, structure, observations
      ├─► weather_skill    → conditions + performance impact
      └─► question_skill   → 1–3 clarifying questions

        [Frontend shows results — user answers questions in modal]

Phase 2 — /api/analyze/coach:
  analysis + weather + user_answers
      └─► coaching_skill  → final coaching text + disclaimer
```

---

## Training Plan

```
POST /api/plan/next-session
  profile + calendar (available days/times) + recent_summary
      └─► training_plan_skill → structured week with sessions
```

---

## Auth flow

```
1. React calls GET /api/auth/strava/url
2. User is redirected to Strava OAuth
3. Strava redirects back to /auth/callback?code=…
4. React calls POST /api/auth/strava/callback with code
5. Backend exchanges code for Strava tokens, wraps in JWT, returns it
6. JWT stored in sessionStorage — sent as Bearer token on every API call
```

---

## Shared core (`src/`)

| Module | Role |
|--------|------|
| `src/llm.py` | OpenAI client (configurable base URL for proxies) |
| `src/strava.py` | Strava API wrapper |
| `src/weather.py` | Open-Meteo weather API |
| `src/skills/` | Individual AI pipeline steps |
| `src/config.py` | Environment variables, token limits |
| `prompts/prompts.py` | All LLM prompts — single source of truth |

---

## Key design decisions

- **Stateless JWT auth** — no database, no sessions server-side. Strava tokens are encrypted inside the JWT and sent with every request.
- **Separate skills, not one big prompt** — weather requires a real API call; coaching requires user answers. Sequential skills with a frontend pause between phases.
- **Vite proxy** — React fetches `/api/*` which Vite forwards to `127.0.0.1:8000`. No CORS config needed in development.
