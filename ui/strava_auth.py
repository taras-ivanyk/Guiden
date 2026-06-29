"""Strava OAuth UI helpers — connect button, callback handler, auth status."""
from __future__ import annotations

from urllib.parse import urlencode

import streamlit as st

from src.logging_config import logger

# OAuth constants
_REDIRECT_URI = "http://localhost:8501"
_SCOPE = "read,activity:read_all,profile:read_all"

# Session-state key used to prevent double-processing the same ?code=
_PROCESSED_CODE_KEY = "_strava_oauth_code_processed"


def is_strava_connected() -> bool:
    """Return True if a valid Strava token bundle is stored in the session."""
    return bool(st.session_state.get("strava_tokens"))


def handle_oauth_callback() -> None:
    """Detect and process a Strava OAuth redirect.

    Must be called on every Streamlit render (top of app.py) so it catches
    the ``?code=`` query parameter immediately after the user approves on Strava.
    Does nothing when no ``code`` param is present.
    """
    code = st.query_params.get("code")
    if not code:
        return

    # Prevent double-processing if Streamlit re-renders before rerun
    if st.session_state.get(_PROCESSED_CODE_KEY) == code:
        return

    from src.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
    from src.strava import exchange_code_for_tokens, get_athlete_info

    client_id = STRAVA_CLIENT_ID
    client_secret = STRAVA_CLIENT_SECRET

    if not client_id or not client_secret:
        st.error(
            "STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET missing from .env — "
            "cannot complete Strava connection."
        )
        st.query_params.clear()
        return

    with st.spinner("Connecting to Strava…"):
        try:
            tokens = exchange_code_for_tokens(code, client_id, client_secret)
            athlete = get_athlete_info(tokens["access_token"])

            st.session_state["strava_tokens"] = tokens
            st.session_state["strava_athlete"] = athlete
            st.session_state[_PROCESSED_CODE_KEY] = code

            name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
            logger.info(f"[auth] Strava connected: {name}")

            # Clear the ?code= from the URL so the page looks clean
            st.query_params.clear()
            st.success(f"✅ Connected as **{name}**!")
            st.rerun()
        except Exception as exc:
            logger.error(f"[auth] OAuth callback failed: {exc}")
            st.error(f"Strava connection failed: {exc}")
            st.query_params.clear()


def render_connect_button() -> None:
    """Render the 'Connect with Strava' OAuth link button.

    Builds the Strava authorization URL using the app's client ID and
    renders a full-width link button that opens the Strava consent screen.
    """
    from src.config import STRAVA_CLIENT_ID

    if not STRAVA_CLIENT_ID:
        st.warning("STRAVA_CLIENT_ID not set in .env — cannot show connect button.")
        return

    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": _REDIRECT_URI,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": _SCOPE,
    }
    url = "https://www.strava.com/oauth/authorize?" + urlencode(params)
    st.link_button("🔗 Connect with Strava", url, use_container_width=True)


def render_auth_status() -> None:
    """Render Strava connection status in the sidebar.

    - Connected: shows athlete name and a Disconnect button.
    - Not connected: shows the Connect with Strava button.
    """
    if is_strava_connected():
        athlete = st.session_state.get("strava_athlete", {})
        name = (
            f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
            or "Connected"
        )
        st.caption(f"✅ Strava: **{name}**")
        if st.button(
            "Disconnect Strava",
            key="_strava_disconnect",
            use_container_width=True,
        ):
            st.session_state.pop("strava_tokens", None)
            st.session_state.pop("strava_athlete", None)
            st.session_state.pop(_PROCESSED_CODE_KEY, None)
            st.session_state["activities"] = []
            st.rerun()
    else:
        render_connect_button()
