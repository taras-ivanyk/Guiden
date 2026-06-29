"""Analyze Workout page — Bug 2 fix: uses get_activities_in_range for date queries."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.strava import get_activities_in_range, get_activity_detail
from src.profile import UserProfile
from src.skills import analysis_skill, weather_skill, question_skill, coaching_skill
from src.skills.base import safety_warning
from ui.components import render_disclaimer
from ui.strava_auth import is_strava_connected, render_connect_button


def render(profile: UserProfile) -> None:
    """Render the Analyze Workout page."""
    st.header("Analyze a Cycling Workout")

    # ── Filters ────────────────────────────────────────────────────────────────
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

    # ── Demo pre-load or Strava fetch ─────────────────────────────────────────
    if st.session_state.get("demo_mode"):
        if not st.session_state.activities:
            from mock.mock_data import get_mock_activity
            st.session_state.activities = [get_mock_activity()]
            st.session_state.selected_activity = None
            st.session_state.intermediate_state = None
            st.session_state.questions = []
            st.session_state.final_output = None
        st.info(
            "🎭 **Demo mode** — mock Strava activity pre-loaded. "
            "Toggle off in the sidebar to use real data."
        )
    elif not is_strava_connected():
        st.info(
            "🔗 Connect your Strava account to load real workouts.",
            icon="🚴",
        )
        render_connect_button()
    else:
        if st.button("🔄 Load cycling activities", type="primary"):
            with st.spinner("Fetching activities from Strava…"):
                try:
                    raw = get_activities_in_range(filter_start, filter_end)
                    st.session_state.activities = [
                        a for a in raw
                        if a["distance_km"] >= filter_min_dist
                        and (filter_max_dist == 0 or a["distance_km"] <= filter_max_dist)
                        and a["moving_time_min"] >= filter_min_dur
                        and (filter_max_dur == 0 or a["moving_time_min"] <= filter_max_dur)
                    ]
                    st.session_state.selected_activity = None
                    st.session_state.intermediate_state = None
                    st.session_state.questions = []
                    st.session_state.final_output = None
                    st.success(
                        f"Found **{len(st.session_state.activities)}** cycling activities "
                        f"between {filter_start} and {filter_end}."
                    )
                except Exception as exc:
                    st.error(f"Strava error: {exc}")

    if st.session_state.activities and not st.session_state.selected_activity:
        if not st.session_state.activities:
            st.warning("No cycling activities found for the selected filters.")
        else:
            activity_options = {
                f"{a['date']} | {a['distance_km']} km | {a['moving_time_min']} min | {a['name']}": a["id"]
                for a in st.session_state.activities
            }
            selected_label = st.selectbox(
                "Select a workout to analyse", list(activity_options.keys())
            )
            selected_id = activity_options[selected_label]

            if st.button("📊 Analyse this workout", type="primary"):
                _demo = st.session_state.get("demo_mode")
                try:
                    activity = (
                        next(
                            a for a in st.session_state.activities
                            if str(a["id"]) == str(selected_id)
                        )
                        if _demo
                        else get_activity_detail(selected_id)
                    )
                    st.session_state.selected_activity = activity
                    st.session_state.intermediate_state = None
                    st.session_state.questions = []
                    st.session_state.final_output = None

                    with st.status("🤖 Agent pipeline running…", expanded=True) as _ps:
                        st.write("🔍 **Analysis skill** — classifying workout type and effort…")
                        analysis = analysis_skill(activity, profile)
                        _hint = (analysis.get("structure") or "").split("\n")[0][:80].strip()
                        st.write(f"  ✅ {_hint}" if _hint else "  ✅ Analysis complete")

                        st.write("🌤️ **Weather skill** — fetching historical conditions…")
                        weather = weather_skill(activity)
                        _cond = (weather.get("conditions") or "N/A").split("\n")[0][:80]
                        st.write(f"  ✅ {_cond}")

                        st.write("💬 **Questions skill** — generating clarifying questions…")
                        questions = question_skill(activity, analysis, profile)
                        st.write(f"  ✅ {len(questions)} question(s) generated")

                        _ps.update(
                            label="✅ Pipeline complete — answer the questions below",
                            state="complete",
                            expanded=False,
                        )

                    state = {
                        "activity": activity, "profile": profile,
                        "analysis": analysis, "weather": weather,
                        "questions": questions, "user_answers": None, "final_output": None,
                    }
                    st.session_state.intermediate_state = state
                    st.session_state.questions = questions
                except Exception as exc:
                    st.error(f"Analysis error: {exc}")

    # ── Health safety warning ──────────────────────────────────────────────────
    warn = safety_warning(profile.injuries or "")
    if warn:
        st.warning(warn)

    # ── Intermediate results ───────────────────────────────────────────────────
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

        # Summary bullets (default view — concise)
        analysis = state.get("analysis", {})
        if analysis.get("summary"):
            st.markdown("**Key Takeaways**")
            for bullet in analysis["summary"]:
                st.markdown(f"- {bullet}")

        # Full details hidden in expander (Fix 6)
        with st.expander("🔍 Full analysis details"):
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown("**Structure**")
                st.info(analysis.get("structure") or analysis.get("raw", "—"))
                st.markdown("**Observations**")
                st.info(analysis.get("observations", "—"))
            with dc2:
                st.markdown("**Deviations**")
                st.info(analysis.get("deviations", "—"))
                st.markdown("**Weather**")
                weather = state.get("weather", {})
                if weather:
                    st.caption(weather.get("conditions", "N/A"))
                    st.info(weather.get("likely_impact", "—"))
                else:
                    st.info("Weather data unavailable.")

        laps = activity.get("laps", [])
        if laps:
            with st.expander("🔢 Lap details"):
                st.dataframe(laps, use_container_width=True)

        # Clarifying questions
        if st.session_state.questions:
            st.divider()
            with st.expander("💬 A few questions before your coaching analysis", expanded=True):
                st.caption("Answer as briefly or in as much detail as you like.")
                answers: dict[str, str] = {}
                for i, q in enumerate(st.session_state.questions):
                    answers[q] = st.text_input(q, key=f"q_{i}")

                if st.button("🎯 Get my coaching analysis", type="primary"):
                    with st.status("🧠 Synthesising coaching…", expanded=True) as _cs:
                        try:
                            st.write(
                                "🏅 **Coaching skill** — combining analysis, "
                                "weather, and your answers…"
                            )
                            final_output = coaching_skill(
                                activity=state["activity"],
                                profile=state["profile"],
                                analysis=state["analysis"],
                                weather=state["weather"],
                                user_answers=answers,
                            )
                            _cs.update(label="✅ Done", state="complete", expanded=False)
                            st.session_state.final_output = final_output
                            st.rerun()
                        except Exception as exc:
                            _cs.update(label="❌ Error", state="error")
                            st.error(f"Coaching error: {exc}")

    # ── Final coaching output ──────────────────────────────────────────────────
    if st.session_state.final_output:
        st.divider()
        st.subheader("🏅 Your Coaching Analysis")
        with st.chat_message("assistant"):
            st.markdown(st.session_state.final_output)
        render_disclaimer()

        if st.button("🔁 Analyse another workout"):
            for k in ["selected_activity", "intermediate_state", "questions", "final_output"]:
                st.session_state[k] = [] if k == "questions" else None
            st.rerun()
