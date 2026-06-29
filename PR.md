# PR: feat/new_UI_with_React → dev

## Summary
Migrates Guiden from Streamlit to a React + Vite + TypeScript frontend backed by a FastAPI layer. Includes full UI redesign, Strava OAuth, bug fixes, and project cleanup.

## Type
- [x] feat
- [x] fix
- [x] migrate
- [x] chore

## Changes

### React frontend
- Vite + React 18 + TypeScript scaffold in `frontend/`
- Auth: `AuthContext` (JWT in `sessionStorage`) + `StravaCallback` (OAuth handler)
- Pages: Home, Analyze, Plan, Profile — all connected to FastAPI via Vite proxy (`/api/* → 127.0.0.1:8000`)
- Components: `DateRangePicker` (inline calendar + presets), `QuestionsModal` (answers → refine coaching), `Sidebar`, `Layout`, `AgentPipeline`, `LoadingSpinner`, `ConnectStrava`

### Design system
- Earthy green palette (`#172207` → `#CAC9C7`) — system-adaptive light/dark
- Strava orange restricted to Strava-specific UI; olive CTA for everything else
- Inter font, CSS variables for full theming

### UX improvements
- **Analyze**: date range calendar picker, 2-column results grid (Analysis | Weather), questions modal to refine coaching
- **Plan**: split-screen layout — form stays visible while result renders alongside; duration pill badges; time input overflow fixed
- **Home**: feature card grid

### FastAPI backend
- 13 endpoints across `auth`, `strava`, `analyze`, `plan`, `race`, `session` routers
- Stateless JWT auth (python-jose HS256) — no database
- `answers: dict[str, str]` wired through coaching pipeline

### Bug fixes
- Vite proxy `localhost` → `127.0.0.1` (macOS IPv6 mismatch causing 500s)
- `AuthCallbackResponse` field `token` → `jwt` (mismatch caused `"undefined"` stored as token → all API calls 401)
- `avg_hr`, `max_hr`, `avg_watts` changed to `float` in Pydantic model (Strava returns fractional values)
- `AnalyzeCoachResponse` field corrected to `coaching_output`
- `JWT_SECRET` added to `.env`

### Project cleanup
- Deleted `ui/` and `app.py` (Streamlit fully replaced)
- Removed `streamlit` from `requirements.txt`
- Added `scripts/dev.sh` — one command starts both servers (`./scripts/dev.sh`)
- Rewrote `README.md`, `docs/overview.md`, `Roadmap.md`
- Updated `copilot-instructions.md`

## How to test
```bash
./scripts/dev.sh
# Frontend → http://localhost:5173
# API docs → http://localhost:8000/docs
```
1. Click **Connect with Strava**
2. Go to **Analyze** → pick a date range → select a ride → Analyze
3. Click **Answer Questions** → fill in answers → Refine Analysis
4. Go to **Plan** → set availability → Generate Plan

## Checklist
- [x] Targets `dev` (not `main`)
- [x] Tests: `pytest backend/tests/ -q` — 11/11 passing
- [x] No secrets committed
- [x] Docs updated (README, overview, Roadmap)
