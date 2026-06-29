"""Home / landing page."""
import streamlit as st
# Імпортуємо нашу функцію кнопок (перевір правильність назви файлу components)
from ui.components import render_disclaimer, render_sport_selector

def render() -> None:
    """Render the landing page."""
    st.title("Guiden")
    st.markdown("*Your personal AI endurance coach — powered by Strava.*")
    
    # Виводимо три кнопки-прямокутники
    render_sport_selector("home")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="feature-card">
            <h3>🔍 Analyze Workout</h3>
            <p>Connect Strava and get a deep-dive coaching analysis of any ride —
            power zones, weather impact, pacing, and a concrete next-step recommendation.
            The coach asks clarifying questions before giving advice.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="feature-card">
            <h3>📅 Training Plan</h3>
            <p>Set your weekly schedule in the calendar, fill in your goal,
            and get a personalized multi-week plan that respects your availability,
            fitness, and sleep.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    profile_data = st.session_state.get("profile_data", {})
    if not profile_data.get("goal"):
        st.info(
            "👉 **Start here:** go to **Profile** in the sidebar — "
            "add your age, FTP, and goal before running an analysis.",
            icon="👤",
        )
    else:
        st.success(
            f"👋 Profile loaded — goal: *{profile_data['goal']}*. "
            "Pick **Analyze Workout** or **Training Plan** from the sidebar.",
            icon="✅",
        )
<<<<<<< HEAD
        st.markdown(
            """
            | Race Prep | Phases your training toward a target event |

            Every output is grounded in your actual data — the coach never invents numbers.
            """
        )

    render_disclaimer()
=======
>>>>>>> origin/dev
