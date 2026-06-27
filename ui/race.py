"""Race Prep page — Fix 4 (race types) + Fix 5 (fitness options) + chat expansion."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.profile import UserProfile
from src.orchestrator import run_race_prep, expand_race_section
from src.skills.base import safety_warning
from ui.components import render_disclaimer
from ui.plan import FITNESS_OPTIONS, _FITNESS_MAP

# Fix 4: simplified race type options
RACE_TYPES = ["Road race", "Time trial"]


def render(profile: UserProfile) -> None:
    """Render the Race Prep page."""
    st.header("Race Preparation Plan")
    st.caption(
        "High-level phased plan toward your target event. "
        "Ask follow-up questions to expand any phase in detail."
    )

    # Health safety warning
    warn = safety_warning(profile.injuries or "")
    if warn:
        st.warning(warn)

    with st.form("race_form"):
        st.subheader("Race Details")
        rf1, rf2 = st.columns(2)
        with rf1:
            # Fix 4: Road race / Time trial only
            race_type = st.selectbox("Race type", RACE_TYPES)
            race_date = st.date_input(
                "Race date", value=date.today() + timedelta(weeks=12)
            )
            race_dist = st.number_input(
                "Expected distance (km)", 0.0, 500.0, 100.0, step=5.0
            )
        with rf2:
            race_elev = st.number_input(
                "Expected elevation gain (m)", 0, 8000, 1000, step=100
            )
            race_wh = st.number_input(
                "Available weekly training hours", 2.0, 30.0, 8.0, step=0.5
            )
            race_goal = st.text_area(
                "Goal", placeholder="e.g. Finish top 20%, beat 5 h", height=80
            )

        # Fix 5: simpler fitness options
        race_fitness_label = st.selectbox("Current fitness", FITNESS_OPTIONS, index=1)
        race_fitness = _FITNESS_MAP[race_fitness_label]

        gen_race = st.form_submit_button("🏁 Generate Race Plan", type="primary")

    if gen_race:
        race_inputs = {
            "race_type": race_type,
            "race_date": race_date.strftime("%Y-%m-%d"),
            "distance_km": float(race_dist),
            "elevation_m": int(race_elev),
            "weekly_hours": float(race_wh),
            "goal": race_goal,
            "current_fitness": race_fitness,
        }
        with st.spinner("Generating your race preparation plan…"):
            try:
                plan_text = run_race_prep(profile, race_inputs)
                st.session_state.race_plan = plan_text
                st.session_state.race_chat = [{"role": "assistant", "content": plan_text}]
            except Exception as exc:
                st.error(f"Error: {exc}")

    # ── Chat interface ─────────────────────────────────────────────────────────
    if st.session_state.race_chat:
        st.divider()
        st.subheader("🗓️ Your Race Preparation Plan")
        for msg in st.session_state.race_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        render_disclaimer()

        follow_up = st.chat_input(
            "Ask to expand any section — e.g. 'Expand the build phase' or 'What should taper look like?'"
        )
        if follow_up:
            st.session_state.race_chat.append({"role": "user", "content": follow_up})
            with st.spinner("Expanding section…"):
                try:
                    expanded = expand_race_section(
                        current_plan=st.session_state.race_plan,
                        user_question=follow_up,
                    )
                    st.session_state.race_chat.append(
                        {"role": "assistant", "content": expanded}
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")
