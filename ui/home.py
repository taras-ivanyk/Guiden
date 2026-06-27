"""Home / landing page."""
import streamlit as st
from ui.components import render_disclaimer


def render() -> None:
    """Render the landing page with feature cards and get-started guidance."""
    st.title("🚴 AI Cycling Coach")
    st.subheader("Your data-driven personal cycling coach — powered by Strava & OpenAI")
    st.divider()

    # Feature cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="feature-card">
            <h3>🔍 Analyze Workout</h3>
            <p>Connect your Strava account and get a deep-dive coaching analysis
            of any ride — power zones, weather impact, pacing, and a concrete
            next-step recommendation. The coach asks you clarifying questions
            before giving advice.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="feature-card">
            <h3>📅 Training Plan</h3>
            <p>Generate a personalized multi-week cycling plan that respects
            your available days and hours, applies progressive overload, and
            accounts for health conditions. Drill into any day for a full
            session breakdown — warm-up, intervals, cooldown, fueling.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="feature-card">
            <h3>🏁 Race Prep <span style="background:#e3f2fd;color:#1565c0;border-radius:4px;
            padding:1px 6px;font-size:0.72em;font-weight:600;">BETA</span></h3>
            <p>Set your target event and get a high-level phased preparation
            plan (Base → Build → Peak → Taper). Ask follow-up questions to
            expand any phase with full session detail.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Get started
    st.markdown("### 👉 Get started")
    st.info(
        "**1.** Fill in your profile in the sidebar (age, FTP, goal, any health conditions).  \n"
        "**2.** Choose a mode from the sidebar navigation.  \n"
        "**3.** Connect Strava or fill in your training details and let the coach go to work.",
        icon="🚴",
    )

    st.divider()

    # What makes this agentic
    with st.expander("ℹ️ How it works (agentic design)"):
        st.markdown(
            """
            This is **not** a single prompt. It orchestrates multiple specialised agents:

            | Agent | Role |
            |-------|------|
            | Analysis | Identifies workout type, deviations from expected effort |
            | Weather | Fetches real historical weather and assesses performance impact |
            | Questions | Asks you 1–3 targeted clarifying questions before drawing conclusions |
            | Coaching | Synthesises everything into grounded, actionable advice |
            | Training Plan | Builds a periodised multi-week plan with progressive overload |
            | Session Expander | Generates full session detail on-demand (lazy, token-efficient) |
            | Race Prep | Phases your training toward a target event |

            Every output is grounded in your actual data — the coach never invents numbers.
            """
        )

    render_disclaimer()
