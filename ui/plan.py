"""Training Plan page — includes calendar availability + clickable day expansion."""
from __future__ import annotations

import streamlit as st

from src.profile import UserProfile
from src.strava import get_recent_summary
from src.orchestrator import run_training_plan
from src.skills.expand_session import expand_session_skill
from src.skills.base import safety_warning
from src.config import DEFAULT_WEEKS_AHEAD
from ui.components import render_disclaimer
from ui.calendar import render_calendar

# Fitness label → internal description for prompts
_FITNESS_MAP = {
    "Not training for a long time": "Beginner / returning after long break",
    "Training 3-4 times a week": "Intermediate, consistent base fitness",
    "Training 5-6 times a week": "Advanced, high training volume",
    "Competitive / racing regularly": "Elite / competitive racer",
}

FITNESS_OPTIONS = list(_FITNESS_MAP.keys())


def render(profile: UserProfile) -> None:
    """Render the Training Plan page."""
    st.header("Build Your Cycling Training Plan")

    # Health safety warning
    warn = safety_warning(profile.injuries or "")
    if warn:
        st.warning(warn)

    # ── Weekly availability calendar ───────────────────────────────────────────
    availability = render_calendar()
    st.divider()

    # ── Plan inputs form ───────────────────────────────────────────────────────
    with st.form("plan_form"):
        st.subheader("Plan Details")
        pf1, pf2 = st.columns(2)
        with pf1:
            days_per_week = st.slider("Training days / week", 1, 7, 4)
            hours_per_day = st.number_input(
                "Hours available per day", 0.5, 6.0, 1.5, step=0.5
            )
            weeks = st.number_input(
                "Plan length (weeks)", min_value=1, max_value=12,
                value=DEFAULT_WEEKS_AHEAD, step=1,
            )
        with pf2:
            plan_goal = st.text_area(
                "Goal",
                placeholder="e.g. Improve FTP by 20 W, finish 100 km gran fondo",
                height=80,
            )
            # Fix 5: simplified fitness options
            plan_exp_label = st.selectbox("Current fitness", FITNESS_OPTIONS, index=1)
            plan_exp = _FITNESS_MAP[plan_exp_label]
            sleep_hours = st.number_input(
                "Avg sleep (hours/night)", 4.0, 10.0, 7.5, step=0.5
            )
        plan_injuries = st.text_area(
            "Injuries / contraindications", height=60,
            placeholder="e.g. Lower back issues, avoid long climbs",
        )

        cb1, cb2 = st.columns(2)
        with cb1:
            gen_plan = st.form_submit_button(
                "🗓️ Generate Multi-Week Plan", type="primary", use_container_width=True
            )
        with cb2:
            gen_next = st.form_submit_button(
                "⚡ Just my next session", use_container_width=True
            )

    if gen_plan or gen_next:
        plan_inputs = {
            "days_per_week": int(days_per_week),
            "hours_per_day": float(hours_per_day),
            "goal": plan_goal,
            "experience": plan_exp,
            "sleep_hours": float(sleep_hours),
            "injuries": plan_injuries or (profile.injuries or ""),
            "weeks": int(weeks),
        }
        if st.session_state.get("demo_mode"):
            from mock.mock_data import get_mock_recent_summary
            recent_summary = get_mock_recent_summary()
        else:
            with st.spinner("Fetching recent training data…"):
                try:
                    recent_summary = get_recent_summary(days=14)
                except Exception:
                    recent_summary = {}

        if gen_next:
            with st.spinner("Generating next session recommendation…"):
                try:
                    result = run_training_plan(
                        profile, plan_inputs, recent_summary,
                        next_only=True, availability=availability,
                    )
                    st.session_state.next_session = result.get("next_session")
                    st.session_state.training_plan = None
                except Exception as exc:
                    st.error(f"Error: {exc}")

        if gen_plan:
            with st.spinner("Building your multi-week training plan…"):
                try:
                    result = run_training_plan(
                        profile, plan_inputs, recent_summary,
                        next_only=False, availability=availability,
                    )
                    st.session_state.next_session = result.get("next_session")
                    st.session_state.training_plan = result.get("training_plan")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ── Next session output ────────────────────────────────────────────────────
    if st.session_state.next_session:
        st.divider()
        st.subheader("⚡ Recommended Next Session")
        with st.chat_message("assistant"):
            st.markdown(st.session_state.next_session)
        render_disclaimer()

    # ── Multi-week plan output ─────────────────────────────────────────────────
    if st.session_state.training_plan:
        st.divider()
        st.subheader("🗓️ Your Multi-Week Training Plan")
        plan_data = st.session_state.training_plan

        if isinstance(plan_data, list):
            for week in plan_data:
                wn = week.get("week_num", "?")
                focus = week.get("focus", "")
                th = week.get("total_hours", "?")
                with st.expander(f"Week {wn}: {focus} — {th}h", expanded=(wn == 1)):
                    # Feature 7: clickable days
                    for session in week.get("sessions", []):
                        day = session.get("day", "?")
                        s_key = f"expanded_{wn}_{day}"

                        row_c, btn_c = st.columns([5, 1])
                        with row_c:
                            st.markdown(
                                f"**{day}** — {session.get('type')} | "
                                f"{session.get('duration_min')} min | "
                                f"*{session.get('intensity')}*"
                            )
                        with btn_c:
                            if st.button("Details", key=f"btn_{wn}_{day}"):
                                if s_key not in st.session_state:
                                    with st.spinner(f"Loading {day} details…"):
                                        detail = expand_session_skill(
                                            wn, day, session, profile
                                        )
                                        st.session_state[s_key] = detail

                        # Show expanded detail if cached
                        if s_key in st.session_state:
                            with st.expander(f"📋 {day} — full session instructions", expanded=True):
                                st.markdown(st.session_state[s_key])

                    rec = week.get("recovery_days", [])
                    if rec:
                        st.caption(f"Rest / recovery: {', '.join(str(d) for d in rec)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(str(plan_data))

        render_disclaimer()
