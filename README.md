# Guiden — AI Cycling Coach

Your data-driven personal cycling coach, powered by Strava + OpenAI.

---

## What it does

Pick a ride → get deep coaching analysis. Set your schedule → get a personalised training plan. Everything is grounded in your real Strava data, never hallucinated.

---

## Architecture

```
Browser (React + Vite :5173)
    │  Vite proxy
    ▼
FastAPI (:8000)
    ├── /api/auth/*    → Strava OAuth · JWT (stateless)
    ├── /api/strava/*  → Strava REST API
    ├── /api/analyze/* → src/skills/ → OpenAI
    └── /api/plan/*    → src/skills/ → OpenAI
```

```
src/
├── llm.py             OpenAI client
├── strava.py          Strava API wrapper
├── weather.py         Open-Meteo weather
├── skills/            AI pipeline steps (analysis, coaching, plan…)
└── config.py          Environment config

backend/
├── main.py            FastAPI app + CORS
├── routers/           API endpoints
├── models/            Pydantic request/response models
├── deps.py            JWT dependency
└── middleware/auth.py JWT sign/verify

frontend/
└── src/
    ├── api/           Typed fetch wrappers
    ├── auth/          JWT context + Strava OAuth callback
    ├── components/    Sidebar, Layout, DateRangePicker, QuestionsModal…
    └── pages/         Home, Analyze, Plan, Profile
```

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd guiden

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd frontend && npm install && cd ..
```

### 2. Configure `.env`

```bash
cp .env.example .env   # then fill in your values
```

Required variables:

| Key | Description |
|-----|-------------|
| `OPENAI_API_KEY` | Your OpenAI key |
| `OPENAI_BASE_URL` | Optional — custom proxy base URL |
| `STRAVA_CLIENT_ID` | From strava.com/settings/api |
| `STRAVA_CLIENT_SECRET` | From strava.com/settings/api |
| `JWT_SECRET` | Any random string ≥ 32 chars (`openssl rand -hex 32`) |

### 3. Run

```bash
./scripts/dev.sh
```

Opens both servers. Press **Ctrl+C** to stop everything.

- Frontend → http://localhost:5173
- API docs → http://localhost:8000/docs

### 4. Connect Strava

Click **Connect with Strava** in the app. You'll be redirected to Strava and back — the app stores your JWT in the session.

---

## Running tests

```bash
pytest backend/tests/ -q
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, TypeScript |
| Backend | FastAPI, Uvicorn, Pydantic v2 |
| Auth | Strava OAuth 2.0, JWT (python-jose HS256) |
| AI | OpenAI gpt-4o-mini, LangGraph skills |
| Data | Strava REST API, Open-Meteo weather |
