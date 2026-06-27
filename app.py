"""Streamlit UI — AI Endurance Coach."""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.strava import get_recent_activities, get_activity_detail
from src.profile import UserProfile, DISCLAIMER
from src.orchestrator import run_analysis_phase, run_coaching_phase

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Endurance Coach",
    page_icon="🏃",
    layout="wide",
)

st.title("🏃 AI Endurance Coach")
st.caption("Agentic workout analysis powered by Strava + OpenAI")

# ---------------------------------------------------------------------------
# Sidebar — Athlete profile
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Your Profile")

    age = st.number_input("Age", min_value=10, max_value=100, value=30, step=1)
    goal = st.text_input("Primary goal", placeholder="e.g. Sub-4h marathon")
    experience = st.selectbox(
        "Experience level",
        ["Beginner", "Intermediate", "Advanced", "Elite"],
        index=1,
    )
    injuries = st.text_area(
        "Injuries / limitations", placeholder="e.g. Left knee tendinopathy", height=68
    )
    notes = st.text_area(
        "Other notes for your coach", placeholder="e.g. Typically train 6h/week", height=68
    )

    profile = UserProfile(
        age=int(age),
        goal=goal,
        experience=experience,
        injuries=injuries,
        notes=notes,
    )

    st.divider()
    st.caption(DISCLAIMER)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "activities" not in st.session_state:
    st.session_state.activities = []
if "selected_activity" not in st.session_state:
    st.session_state.selected_activity = None
if "intermediate_state" not in st.session_state:
    st.session_state.intermediate_state = None
if "questions" not in st.session_state:
    st.session_state.questions = []
if "final_output" not in st.session_state:
    st.session_state.final_output = None

# ---------------------------------------------------------------------------
# Step 1 — Load activities
# ---------------------------------------------------------------------------

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🔄 Load my Strava activities", type="primary"):
        with st.spinner("Connecting to Strava…"):
            try:
                st.session_state.activities = get_recent_activities(limit=10)
                st.session_state.selected_activity = None
                st.session_state.intermediate_state = None
                st.session_state.questions = []
                st.session_state.final_output = None
            except Exception as e:
                st.error(f"Strava error: {e}")

# ---------------------------------------------------------------------------
# Step 2 — Pick an activity
# ---------------------------------------------------------------------------

if st.session_state.activities:
    activity_options = {
        f"{a['date']} | {a['type']} | {a['distance_km']} km | {a['name']}": a["id"]
        for a in st.session_state.activities
    }

    selected_label = st.selectbox(
        "Select a workout to analyze",
        options=list(activity_options.keys()),
    )
    selected_id = activity_options[selected_label]

    if st.button("📊 Analyse this workout"):
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

            except Exception as e:
                st.error(f"Analysis error: {e}")

# ---------------------------------------------------------------------------
# Step 3 — Show intermediate results + questions
# ---------------------------------------------------------------------------

if st.session_state.intermediate_state and not st.session_state.final_output:
    state = st.session_state.intermediate_state
    activity = st.session_state.selected_activity

    st.divider()
    st.subheader(f"📋 Analysis: {activity.get('name')}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Workout Structure & Observations**")
        analysis = state.get("analysis", {})
        st.info(analysis.get("raw", "No analysis available."))

    with col_b:
        st.markdown("**Weather Conditions & Impact**")
        weather = state.get("weather", {})
        if weather:
            st.markdown(f"*Conditions:* {weather.get('conditions', 'N/A')}")
            st.info(weather.get("likely_impact", "No weather impact assessment."))
        else:
            st.info("Weather data unavailable.")

    # Lap table
    laps = activity.get("laps", [])
    if laps:
        st.markdown("**Laps**")
        st.dataframe(laps, use_container_width=True)

    # Clarifying questions
    if st.session_state.questions:
        st.divider()
        st.subheader("💬 A few questions before your coaching analysis")
        st.caption("Answer as briefly or in as much detail as you like.")

        answers: dict[str, str] = {}
        for i, q in enumerate(st.session_state.questions):
            answer = st.text_input(q, key=f"q_{i}")
            answers[q] = answer

        if st.button("🎯 Get my coaching analysis", type="primary"):
            with st.spinner("Synthesizing coaching feedback…"):
                try:
                    final_state = run_coaching_phase(state, answers)
                    st.session_state.final_output = final_state.get("final_output", "")
                    st.rerun()
                except Exception as e:
                    st.error(f"Coaching error: {e}")

# ---------------------------------------------------------------------------
# Step 4 — Final coaching output
# ---------------------------------------------------------------------------

if st.session_state.final_output:
    st.divider()
    st.subheader("🏅 Your Coaching Analysis")
    st.markdown(st.session_state.final_output)

    st.divider()
    st.warning(DISCLAIMER)

    if st.button("🔁 Analyze another workout"):
        for key in ["activities", "selected_activity", "intermediate_state",
                    "questions", "final_output"]:
            st.session_state[key] = [] if key in ("activities", "questions") else None
        st.rerun()
