"""On-demand detailed session expansion skill (lazy — only called on user click)."""
from src.profile import UserProfile
from src.llm import chat
from src.skills.base import health_block
from prompts.prompts import EXPAND_SESSION_PROMPT
from src.logging_config import logger


def expand_session_skill(
    week_num: int,
    day: str,
    session: dict,
    profile: UserProfile,
) -> str:
    """Generate a full, detailed breakdown for one training session.

    Called lazily — only when the user clicks a session to expand it.
    Result should be cached in st.session_state to avoid repeat LLM calls.

    Args:
        week_num: Week number in the training plan.
        day: Day of the week (e.g. "Monday").
        session: Session dict with type, duration_min, intensity.
        profile: Athlete's UserProfile.

    Returns:
        Detailed session instructions as text.
    """
    logger.info(
        f"[expand_session_skill] Expanding Week {week_num} — {day} — {session.get('type')}"
    )
    user_msg = (
        f"Week {week_num}, {day}\n"
        f"Session type: {session.get('type')}\n"
        f"Duration: {session.get('duration_min')} min\n"
        f"Target intensity: {session.get('intensity')}\n\n"
        f"Athlete profile:\n{profile.to_context()}"
        + health_block(profile.injuries or "")
    )
    return chat(EXPAND_SESSION_PROMPT, user_msg, skill="expand_session")
