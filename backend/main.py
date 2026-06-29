"""FastAPI application entry point."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.routers import auth, strava, analyze, plan, race, session

app = FastAPI(
    title="Guiden API",
    description="AI Cycling Coach — FastAPI backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(strava.router,  prefix="/api/strava",  tags=["strava"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(plan.router,    prefix="/api/plan",    tags=["plan"])
app.include_router(race.router,    prefix="/api/race",    tags=["race"])
app.include_router(session.router, prefix="/api/session", tags=["session"])


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "guiden-api"}
