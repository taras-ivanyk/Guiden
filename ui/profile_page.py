"""Athlete profile setup page."""
from __future__ import annotations

import streamlit as st

_EXPERIENCE_OPTIONS = [
    "Beginner / just starting out",
    "Intermediate \u2014 training 3-4 times/week",
    "Advanced \u2014 training 5+ times/week",
    "Competitive / racing regularly",
]


def render() -> None:
    """Render the athlete profile setup form."""
    st.header("\U0001f464 Your Athlete Profile")
    st.caption(
        "Fill this in once. It personalises your coaching analysis and training plans."
    )

    existing: dict = st.session_state.get("profile_data", {})

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input(
                "Age",
                min_value=10,
                max_value=100,
                value=int(existing.get("age", 30)),
                step=1,
            )
            ftp = st.number_input(
                "FTP (W)",
                min_value=0,
                max_value=600,
                value=int(existing.get("ftp") or 0),
                step=5,
                help="Functional Threshold Power \u2014 leave 0 if unknown",
            )
        with c2:
            goal = st.text_input(
                "Primary goal",
                value=existing.get("goal", ""),
                placeholder="e.g. Improve FTP, finish 100 km gran fondo",
            )
            exp_val = existing.get("experience", _EXPERIENCE_OPTIONS[1])
            exp_idx = (
                _EXPERIENCE_OPTIONS.index(exp_val)
                if exp_val in _EXPERIENCE_OPTIONS
                else 1
            )
            experience = st.selectbox("Experience level", _EXPERIENCE_OPTIONS, index=exp_idx)

        injuries = st.text_area(
            "Injuries / health conditions",
            value=existing.get("injuries", ""),
            placeholder="e.g. Lower back pain, heart condition \u2014 be specific",
            height=80,
        )

        saved = st.form_submit_button(
            "\U0001f4be Save Profile", type="primary", use_container_width=True
        )

    if saved:
        st.session_state["profile_data"] = {
            "age": int(age),
            "ftp": int(ftp) if ftp else None,
            "goal": goal,
            "experience": experience,
            "injuries": injuries,
        }
        st.success(
            "\u2705 Profile saved! Use the sidebar to **Analyze a Workout** or **Build a Training Plan**."
        )

    # Summary of current profile
    if existing:
        st.divider()
        st.caption("**Current profile:**")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Age", existing.get("age", "\u2014"))
        mc2.metric("FTP", f"{existing.get('ftp') or '\u2014'} W")
        mc3.metric("Goal", (existing.get("goal") or "\u2014")[:28])
        if existing.get("injuries"):
            st.caption(f"\u26a0\ufe0f Health note: {existing['injuries']}")
