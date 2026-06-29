"""Shared UI helpers — CSS, sidebar, sport selector, token counter, disclaimer."""
from __future__ import annotations

import streamlit as st

from src.profile import UserProfile, DISCLAIMER
from src.llm import get_session_usage

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
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
.feature-card {
    background: #f7f8fa;
    border-radius: 12px;
    padding: 20px 18px;
    border: 1px solid #e0e4ea;
    margin-bottom: 8px;
}
.token-counter {
    font-size: 0.78em;
    color: #888;
    padding: 4px 0;
}
</style>
"""


def inject_css() -> None:
    """Inject custom CSS into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_disclaimer() -> None:
    """Render the safety disclaimer as a styled box."""
    st.markdown(
        f'<div class="disclaimer-box">{DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


def render_sport_selector() -> None:
    """Render the cycling-only sport selector row."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("🚴 Cycling", type="primary", use_container_width=True)
    with c2:
        st.button("🏃 Running — coming soon", disabled=True, use_container_width=True)
    with c3:
        st.button("🏊 Swimming — coming soon", disabled=True, use_container_width=True)


def render_sidebar_profile() -> tuple[UserProfile, str]:
    """Render sidebar navigation and profile form.

    Returns:
        Tuple of (UserProfile, selected_mode_string).
    """
    with st.sidebar:
        st.title("🚴 AI Cycling Coach")
        st.divider()

        mode = st.radio(
            "Navigate",
            ["🏠 Home", "🔍 Analyze Workout", "📅 Training Plan", "🏁 Race Prep ✦ beta"],
            label_visibility="collapsed",
        )
        st.toggle(
            "🎭 Demo mode",
            key="demo_mode",
            help="Pre-loaded mock Strava activity — no account needed. Great for demos.",
        )
        st.divider()

        st.subheader("Your Profile")
        age = st.number_input("Age", min_value=10, max_value=100, value=30, step=1)
        ftp = st.number_input(
            "FTP (W)",
            min_value=0,
            max_value=600,
            value=0,
            step=5,
            help="Functional Threshold Power — leave 0 if unknown",
        )
        goal = st.text_input("Primary goal", placeholder="e.g. Improve FTP, build base")
        experience = st.selectbox(
            "Experience level",
            ["Beginner", "Intermediate", "Advanced", "Elite"],
            index=1,
        )
        injuries = st.text_area(
            "Injuries / health conditions",
            placeholder="e.g. Heart condition, back pain — be specific",
            height=68,
        )
        notes = st.text_area(
            "Other notes",
            placeholder="e.g. Typically train 6h/week",
            height=60,
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
        render_disclaimer()

    return profile, mode


def render_token_counter() -> None:
    """Render a small token/cost counter in the sidebar."""
    usage = get_session_usage()
    if usage["calls"] > 0:
        with st.sidebar:
            st.markdown(
                f'<div class="token-counter">🔢 {usage["tokens"]:,} tokens used this session '
                f'(~${usage["cost"]:.4f}) · {usage["calls"]} call{"s" if usage["calls"] != 1 else ""}</div>',
                unsafe_allow_html=True,
            )
