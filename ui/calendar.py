"""Weekly training availability calendar component."""
from __future__ import annotations

import streamlit as st

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Half-hour increments 00:00 – 23:30
HOURS: list[str] = [
    f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)
]

_DEFAULT_START = "07:00"
_DEFAULT_END = "09:00"


def _compute_duration_min(start: str, end: str) -> int:
    """Return training window length in minutes from HH:MM strings."""
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return (eh * 60 + em) - (sh * 60 + sm)


def _tile_label(day: str, abbr: str, availability: dict[str, dict[str, str]]) -> str:
    """Build the markdown label shown inside a day tile.

    Args:
        day: Full day name (e.g. 'Monday').
        abbr: 3-letter abbreviation shown as the tile header.
        availability: Current saved availability dict.

    Returns:
        Markdown string with day name, time window, and duration (or '\u2014' if unset).
    """
    entry = availability.get(day)
    if entry:
        dur = entry.get("duration_min") or _compute_duration_min(entry["start"], entry["end"])
        h, m = divmod(dur, 60)
        dur_str = f"{h}h" + (f" {m}min" if m else "")
        return f"**{abbr}**  \n\U0001f7e2 {entry['start']}\u2013{entry['end']}  \n*{dur_str}*"
    return f"**{abbr}**  \n—"


def render_calendar() -> dict[str, dict[str, str]]:
    """Render a weekly availability tile calendar and return the saved schedule.

    The user clicks a day tile to select it, then sets a start/end time in the
    edit panel that appears below the tiles.  Changes are persisted in
    ``st.session_state['availability']``.

    Returns:
        Dict mapping day name → ``{"start": "HH:MM", "end": "HH:MM"}``.
        Days with no training window are omitted.
        E.g. ``{"Monday": {"start": "07:00", "end": "09:00"}, ...}``
    """
    st.subheader("📅 Weekly Training Schedule")
    st.caption(
        "Click a day to set your training window. "
        "Green tiles are active; click again to edit."
    )

    # Initialise state
    if "availability" not in st.session_state or not isinstance(
        st.session_state["availability"], dict
    ):
        st.session_state["availability"] = {}
    if "_cal_selected_day" not in st.session_state:
        st.session_state["_cal_selected_day"] = None

    availability: dict[str, dict[str, str]] = st.session_state["availability"]
    selected: str | None = st.session_state["_cal_selected_day"]

    # ── Tile row ──────────────────────────────────────────────────────────────
    cols = st.columns(7)
    for col, day, abbr in zip(cols, DAYS, DAY_ABBR):
        with col:
            label = _tile_label(day, abbr, availability)
            is_selected = day == selected
            # Highlight selected tile with a coloured border via container
            border_color = "#1565c0" if is_selected else (
                "#2e7d32" if day in availability else "#555"
            )
            st.markdown(
                f"""
                <div style="border:2px solid {border_color};
                            border-radius:8px;padding:6px 4px;
                            text-align:center;font-size:0.82em;
                            min-height:56px;">
                {label.replace(chr(10), '<br>')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Invisible button overlaid — clicking sets the selected day
            if st.button(
                "✏️" if is_selected else ("📋" if day in availability else "➕"),
                key=f"_cal_btn_{day}",
                use_container_width=True,
                help=f"Edit {day}",
            ):
                st.session_state["_cal_selected_day"] = (
                    None if is_selected else day
                )
                st.rerun()

    # ── Edit panel ────────────────────────────────────────────────────────────
    if selected:
        st.markdown("---")
        existing = availability.get(selected, {})
        default_start = existing.get("start", _DEFAULT_START)
        default_end = existing.get("end", _DEFAULT_END)

        ep_col1, ep_col2, ep_col3 = st.columns([2, 2, 3])
        with ep_col1:
            start = st.selectbox(
                f"Start — {selected}",
                HOURS,
                index=HOURS.index(default_start) if default_start in HOURS else 14,
                key=f"_cal_start_{selected}",
            )
        with ep_col2:
            # Default end index must be after start
            start_idx = HOURS.index(start)
            default_end_idx = (
                HOURS.index(default_end)
                if default_end in HOURS and HOURS.index(default_end) > start_idx
                else min(start_idx + 4, len(HOURS) - 1)  # +2 h default
            )
            end = st.selectbox(
                "End",
                HOURS,
                index=default_end_idx,
                key=f"_cal_end_{selected}",
            )
        with ep_col3:
            st.markdown("&nbsp;", unsafe_allow_html=True)  # vertical spacer
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("💾 Save", key="_cal_save", type="primary", use_container_width=True):
                    if HOURS.index(end) > HOURS.index(start):
                        availability[selected] = {
                            "start": start,
                            "end": end,
                            "duration_min": _compute_duration_min(start, end),
                        }
                        st.session_state["availability"] = availability
                        st.session_state["_cal_selected_day"] = None
                        st.rerun()
                    else:
                        st.error("End time must be after start time.")
            with btn_col2:
                if st.button("🗑️ Remove", key="_cal_remove", use_container_width=True):
                    availability.pop(selected, None)
                    st.session_state["availability"] = availability
                    st.session_state["_cal_selected_day"] = None
                    st.rerun()

    # ── Summary ───────────────────────────────────────────────────────────────
    if availability:
        st.markdown("---")
        st.caption("**Your training schedule:**")
        summary_parts = []
        for day in DAYS:
            v = availability.get(day)
            if v:
                dur = v.get("duration_min") or _compute_duration_min(v["start"], v["end"])
                h, m = divmod(dur, 60)
                dur_str = f"{h}h" + (f" {m}min" if m else "")
                summary_parts.append(f"{day} {v['start']}\u2013{v['end']} ({dur_str})")
        st.markdown(" &nbsp;|&nbsp; ".join(summary_parts))
    else:
        st.markdown("---")
        st.caption("No training days set yet — click a day tile to add one.")

    return availability
