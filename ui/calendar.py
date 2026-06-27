"""Weekly training availability calendar component."""
from __future__ import annotations

import streamlit as st

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SLOTS = ["Morning", "Afternoon", "Evening"]


def render_calendar() -> dict[str, list[str]]:
    """Render a weekly availability grid and return the selected slots.

    Stores the result in st.session_state["availability"].

    Returns:
        Dict mapping day name → list of selected slot names.
        E.g. {"Monday": ["Morning"], "Wednesday": ["Afternoon", "Evening"]}
    """
    st.subheader("📅 Your Weekly Availability")
    st.caption("Select which days and time slots you can train.")

    availability: dict[str, list[str]] = {}

    for day in DAYS:
        col_day, col_slots = st.columns([2, 4])
        with col_day:
            available = st.checkbox(day, key=f"avail_{day}")
        with col_slots:
            if available:
                slots = st.multiselect(
                    "Slots",
                    SLOTS,
                    default=st.session_state.get(f"slots_{day}", []),
                    key=f"slots_{day}",
                    label_visibility="collapsed",
                )
                availability[day] = slots
            else:
                availability[day] = []

    # Persist in session state
    st.session_state["availability"] = availability
    return availability
