"""Guiden — entry point.

Thin router: sets up page config, session state, and delegates to UI modules.
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from ui.components import inject_css, render_sidebar_profile, render_token_counter, render_sport_selector
from ui import home, analyze, plan, profile_page
from src.profile import UserProfile

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Guiden",
    page_icon="🚴",
    layout="wide",
)
inject_css()

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "activities": [],
    "selected_activity": None,
    "intermediate_state": None,
    "questions": [],
    "final_output": None,
    "training_plan": None,
    "next_session": None,
    "race_plan": None,
    "race_chat": [],
    "availability": {},
    "profile_data": {},
    "demo_mode": False,
    "_session_tokens": 0,
    "_session_cost": 0.0,
    "_session_calls": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
mode = render_sidebar_profile()
render_token_counter()

# ── Profile from session state (set via Profile page) ─────────────────────────────
_pd = st.session_state.get("profile_data", {})
profile = UserProfile(
    age=_pd.get("age", 30),
    ftp=_pd.get("ftp") or None,
    goal=_pd.get("goal", ""),
    experience=_pd.get("experience", "Intermediate"),
    injuries=_pd.get("injuries", ""),
)

# ── Sport selector ────────────────────────────────────────────────────────────────────
render_sport_selector()
st.divider()

# ── Route to page ────────────────────────────────────────────────────────────────────
if mode == "🏠 Home":
    home.render()
elif mode == "🔍 Analyze Workout":
    analyze.render(profile)
elif mode == "📅 Training Plan":
    plan.render(profile)
elif mode == "👤 Profile":
    profile_page.render()
