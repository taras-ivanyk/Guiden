"""Centralised configuration — reads all environment variables with safe defaults."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ──────────────────────────────────────────────────────────────────
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.4"))
MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "1500"))

# Cost per million tokens — gpt-4o-mini defaults
COST_PER_M_INPUT: float = float(os.getenv("COST_PER_M_INPUT", "0.15"))
COST_PER_M_OUTPUT: float = float(os.getenv("COST_PER_M_OUTPUT", "0.60"))

# Per-session token budget; LLM calls are blocked once exceeded
SESSION_TOKEN_BUDGET: int = int(os.getenv("SESSION_TOKEN_BUDGET", "50000"))

# ── Strava ───────────────────────────────────────────────────────────────────
STRAVA_CLIENT_ID: str = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET: str = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_REFRESH_TOKEN: str = os.getenv("STRAVA_REFRESH_TOKEN", "")
TOP_K_ACTIVITIES: int = int(os.getenv("TOP_K_ACTIVITIES", "10"))

# ── Training defaults ────────────────────────────────────────────────────────
DEFAULT_WEEKS_AHEAD: int = int(os.getenv("DEFAULT_WEEKS_AHEAD", "4"))

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
