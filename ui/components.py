"""Shared UI helpers — CSS, sidebar, sport selector, token counter, disclaimer."""
from __future__ import annotations

import streamlit as st

from src.profile import DISCLAIMER
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


def render_sport_selector(page_name: str) -> None:
    """Render the sport selector row with page-specific unique keys."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("🚴 Cycling", type="primary", use_container_width=True, key=f"{page_name}_btn_cycling")
    with c2:
        st.button("🏃 Running — coming soon", disabled=True, use_container_width=True, key=f"{page_name}_btn_running")
    with c3:
        st.button("🏊 Swimming — coming soon", disabled=True, use_container_width=True, key=f"{page_name}_btn_swimming")


def render_sidebar_profile() -> str:
    """Render sidebar navigation.

    Returns:
        Selected navigation mode string.
    """
    from ui.strava_auth import render_auth_status
    with st.sidebar:
        st.title("🚴 Guiden")
        st.divider()

        mode = st.radio(
            "Navigate",
            ["🏠 Home", "🔍 Analyze Workout", "📅 Training Plan", "👤 Profile"],
            label_visibility="collapsed",
        )
        st.toggle(
            "🎭 Demo mode",
            key="demo_mode",
            help="Pre-loaded mock Strava activity — no account needed.",
        )
        st.divider()
        render_auth_status()
        st.divider()
        render_disclaimer()

    return mode


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
