"""Streamlit UI — AI Cycling Coach."""

import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.strava import get_recent_activities, get_activity_detail, get_recent_summary
from src.profile import UserProfile, DISCLAIMER
from src.orchestrator import (
    run_analysis_phase,
    run_coaching_phase,
    run_training_plan,
    run_race_prep,
    expand_race_section,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config + custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Cycling Coach",
    page_icon="🚴",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background: #f7f8fa;
        border-radius: 10px;
        padding: 12px 18px;
        border: 1px solid #e0e4ea;
    }
    .disclaimer-box {
        background: #fff8e1;
        border-left: 4px solid #f9a825;
        padding: 8px 14px;
        border-radius: 4px;
        font-size: 0.82em;
        color: #555;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

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
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Navigation + Athlete profile
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🚴 AI Cycling Coach")
    st.divider()

    mode = st.radio(
        "Navigate",
        ["🔍 Analyze Workout", "📅 Training Plan", "🏁 Race Prep ✦ beta"],
        label_visibility="collapsed",
    )
    st.divider()

    st.subheader("Your Profile")
    age = st.number_input("Age", min_value=10, max_value=100, value=30, step=1)
    ftp = st.number_input(
        "FTP (W)", min_value=0, max_value=600, value=0, step=5,
        help="Functional Threshold Power — leave 0 if unknown",
    )
    goal = st.text_input("Primary goal", placeholder="e.g. Improve FTP, build base")
    experience = st.selectbox(
        "Experience level",
        ["Beginner", "Intermediate", "Advanced", "Elite"],
        index=1,
    )
    injuries = st.text_area(
        "Injuries / limitations", placeholder="e.g. Left knee", height=60
    )
    notes = st.text_area(
        "Other notes", placeholder="e.g. Typically train 6h/week", height=60
    )

    profile = UserProfile(
        age=int(age),
        ftp=int(ftp) if ftp else None,
        goal=goal,
        experience=experience,
        injuries=injuries,
        notes=notes,
    )

    st.divider()
    st.markdown(
        f'<div class="disclaimer-box">{DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Sport selector (cycling only; other sports shown as roadmap items)
# ─────────────────────────────────────────────────────────────────────────────

sc1, sc2, sc3 = st.columns(3)
with sc1:
    st.button("🚴 Cycling", type="primary", use_container_width=True)
with sc2:
    st.button("🏃 Running — coming soon", disabled=True, use_container_width=True)
with sc3:
    st.button("🏊 Swimming — coming soon", disabled=True, use_container_width=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MODE 1 — Analyze Workout
# ─────────────────────────────────────────────────────────────────────────────

if mode == "🔍 Analyze Workout":
    st.header("Analyze a Cycling Workout")

    with st.expander("⚙️ Filters", expanded=False):
        fc1, fc2 = st.columns(2)
        with fc1:
            filter_start = st.date_input(
                "Start date", value=date.today() - timedelta(days=90)
            )
            filter_min_dist = st.number_input(
                "Min distance (km)", min_value=0.0, value=0.0, step=1.0
            )
            filter_min_dur = st.number_input(
                "Min duration (min)", min_value=0.0, value=0.0, step=5.0
            )
        with fc2:
            filter_end = st.date_input("End date", value=date.today())
            filter_max_dist = st.number_input(
                "Max distance (km)", min_value=0.0, value=0.0, step=1.0,
                help="0 = no limit",
            )
            filter_max_dur = st.number_input(
                "Max duration (min)", min_value=0.0, value=0.0, step=5.0,
                help="0 = no limit",
            )

    if st.button("🔄 Load my cycling activities", type="primary"):
        with st.spinner("Connecting to Strava…"):
            try:
                st.session_state.activities = get_recent_activities()
                st.session_state.selected_activity = None
                st.session_state.intermediate_state = None
                st.session_state.questions = []
                st.session_state.final_output = None
            except Exception as exc:
                st.error(f"Strava error: {exc}")

    # Apply client-side filters
    filtered = [
        a for a in st.session_state.activities
        if (
            filter_start.strftime("%Y-%m-%d") <= a["date"] <= filter_end.strftime("%Y-%m-%d")
            and a["distance_km"] >= filter_min_dist
            and (filter_max_dist == 0 or a["distance_km"] <= filter_max_dist)
            and a["moving_time_min"] >= filter_min_dur
            and (filter_max_dur == 0 or a["moving_time_min"] <= filter_max_dur)
        )
    ]

    if st.session_state.activities and not filtered:
        st.warning("No activities match the current filters.")

    if filtered:
        activity_options = {
            f"{a['date']} | {a['distance_km']} km | {a['moving_time_min']} min | {a['name']}": a["id"]
            for a in filtered
        }
        selected_label = st.selectbox(
            "Select a workout to analyze", list(activity_options.keys())
        )
        selected_id = activity_options[selected_label]

        if st.button("📊 Analyse this workout", type="primary"):
            with st.spinner("Fetching activity detail and running analysis…"):
                try:
                    activity = get_activity_detail(selected_id)
                    st.session_state.selected_activity = activity
                    st.session_state.intermediate_state = None
                    st.session_state.questions = []
                    st.session_state.final_output = None

                    state = run_analysis_phase(activity, profile)
                    st.session_state.intermediate_state = state
                    st.session_state.questions = state.get("questions") or []
                except Exception as exc:
                    st.error(f"Analysis error: {exc}")

    # ── Intermediate results ──
    if st.session_state.intermediate_state and not st.session_state.final_output:
        state = st.session_state.intermediate_state
        activity = st.session_state.selected_activity

        st.divider()
        st.subheader(f"📋 {activity.get('name')} — {activity.get('date')}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Distance", f"{activity.get('distance_km', 0)} km")
        m2.metric("Duration", f"{activity.get('moving_time_min', 0)} min")
        m3.metric("Avg Power", f"{activity.get('avg_watts') or 'N/A'} W")
        m4.metric("Avg HR", f"{activity.get('avg_hr') or 'N/A'} bpm")

        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown("**Workout Structure & Observations**")
            st.info(state.get("analysis", {}).get("raw", "No analysis available."))
        with ac2:
            st.markdown("**Weather Conditions & Impact**")
            weather = state.get("weather", {})
            if weather:
                st.caption(weather.get("conditions", "N/A"))
                st.info(weather.get("likely_impact", "No weather impact assessment."))
            else:
                st.info("Weather data unavailable.")

        laps = activity.get("laps", [])
        if laps:
            with st.expander("🔢 Lap details"):
                st.dataframe(laps, use_container_width=True)

        if st.session_state.questions:
            st.divider()
            with st.expander("💬 A few questions before your coaching analysis", expanded=True):
                st.caption("Answer as briefly or in as much detail as you like.")
                answers: dict[str, str] = {}
                for i, q in enumerate(st.session_state.questions):
                    answers[q] = st.text_input(q, key=f"q_{i}")

                if st.button("🎯 Get my coaching analysis", type="primary"):
                    with st.spinner("Synthesizing coaching feedback…"):
                        try:
                            final_state = run_coaching_phase(state, answers)
                            st.session_state.final_output = final_state.get("final_output", "")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Coaching error: {exc}")

    # ── Final coaching output ──
    if st.session_state.final_output:
        st.divider()
        st.subheader("🏅 Your Coaching Analysis")
        with st.chat_message("assistant"):
            st.markdown(st.session_state.final_output)
        st.markdown(
            f'<div class="disclaimer-box">{DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔁 Analyze another workout"):
            st.session_state.selected_activity = None
            st.session_state.intermediate_state = None
            st.session_state.questions = []
            st.session_state.final_output = None
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MODE 2 — Training Plan
# ─────────────────────────────────────────────────────────────────────────────

elif mode == "📅 Training Plan":
    st.header("Build Your Cycling Training Plan")

    default_weeks = int(os.getenv("DEFAULT_WEEKS_AHEAD", "4"))

    with st.form("plan_form"):
        st.subheader("Plan Inputs")
        pf1, pf2 = st.columns(2)
        with pf1:
            days_per_week = st.slider("Training days / week", 1, 7, 4)
            hours_per_day = st.number_input(
                "Hours available per day", 0.5, 6.0, 1.5, step=0.5
            )
            weeks = st.number_input(
                "Plan length (weeks)", min_value=1, max_value=12,
                value=default_weeks, step=1,
            )
        with pf2:
            plan_goal = st.text_area(
                "Goal",
                placeholder="e.g. Improve FTP by 20 W, finish 100 km gran fondo",
                height=80,
            )
            plan_exp = st.selectbox(
                "Current fitness / experience",
                [
                    "Just getting back into it",
                    "Regularly cycling 3-4×/week",
                    "Well-trained, racing occasionally",
                    "Competitive / high volume",
                ],
                index=1,
            )
            sleep_hours = st.number_input(
                "Avg sleep (hours/night)", 4.0, 10.0, 7.5, step=0.5
            )
        plan_injuries = st.text_area(
            "Injuries / contraindications", height=60,
            placeholder="e.g. Lower back issues",
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            gen_plan = st.form_submit_button(
                "🗓️ Generate Multi-Week Plan", type="primary", use_container_width=True
            )
        with col_btn2:
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
            "injuries": plan_injuries,
            "weeks": int(weeks),
        }
        with st.spinner("Fetching recent training data…"):
            try:
                recent_summary = get_recent_summary(days=14)
            except Exception:
                recent_summary = {}

        if gen_next:
            with st.spinner("Generating next session recommendation…"):
                try:
                    result = run_training_plan(
                        profile, plan_inputs, recent_summary, next_only=True
                    )
                    st.session_state.next_session = result.get("next_session")
                    st.session_state.training_plan = None
                except Exception as exc:
                    st.error(f"Error: {exc}")

        if gen_plan:
            with st.spinner("Building your multi-week training plan…"):
                try:
                    result = run_training_plan(
                        profile, plan_inputs, recent_summary, next_only=False
                    )
                    st.session_state.next_session = result.get("next_session")
                    st.session_state.training_plan = result.get("training_plan")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    if st.session_state.next_session:
        st.divider()
        st.subheader("⚡ Recommended Next Session")
        with st.chat_message("assistant"):
            st.markdown(st.session_state.next_session)
        st.markdown(
            f'<div class="disclaimer-box">{DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )

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
                    for s in week.get("sessions", []):
                        st.markdown(
                            f"- **{s.get('day', '')} — {s.get('type', '')}**: "
                            f"{s.get('duration_min', '')} min | *{s.get('intensity', '')}*"
                        )
                    rec = week.get("recovery_days", [])
                    if rec:
                        st.caption(f"Rest / recovery: {', '.join(str(d) for d in rec)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(str(plan_data))
        st.markdown(
            f'<div class="disclaimer-box">{DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# MODE 3 — Race Prep
# ─────────────────────────────────────────────────────────────────────────────

elif mode == "🏁 Race Prep ✦ beta":
    st.header("Race Preparation Plan")
    st.caption(
        "High-level phased plan toward your target event. "
        "Ask follow-up questions to expand any phase."
    )

    with st.form("race_form"):
        st.subheader("Race Details")
        rf1, rf2 = st.columns(2)
        with rf1:
            race_type = st.selectbox(
                "Race type",
                [
                    "Long group race (e.g. 200 km gran fondo)",
                    "Time trial (e.g. 10 km road TT)",
                ],
            )
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

        race_fitness = st.selectbox(
            "Current fitness",
            [
                "Just getting back into it",
                "Regularly cycling 3-4×/week",
                "Well-trained, racing occasionally",
                "Competitive / high volume",
            ],
            index=1,
        )
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
                st.session_state.race_chat = [
                    {"role": "assistant", "content": plan_text}
                ]
            except Exception as exc:
                st.error(f"Error: {exc}")

    if st.session_state.race_chat:
        st.divider()
        st.subheader("🗓️ Your Race Preparation Plan")
        for msg in st.session_state.race_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        st.markdown(
            f'<div class="disclaimer-box">{DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )
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
