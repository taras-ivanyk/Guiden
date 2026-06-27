"""Central LLM client — every skill routes through here.

Automatically logs model name, token counts, and estimated cost per call.
Enforces the SESSION_TOKEN_BUDGET; blocks further calls when exceeded.
Maintains per-session counters in st.session_state.
"""
from __future__ import annotations

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import (
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    LLM_TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    SESSION_TOKEN_BUDGET,
    COST_PER_M_INPUT,
    COST_PER_M_OUTPUT,
)
from src.logging_config import logger

# Session-state keys
_KEY_TOKENS = "_session_tokens"
_KEY_COST = "_session_cost"
_KEY_CALLS = "_session_calls"


def _client() -> ChatOpenAI:
    """Build a ChatOpenAI client from current config."""
    kwargs: dict = {
        "model": OPENAI_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def chat(system: str, user: str, skill: str = "unknown") -> str:
    """Run a system+user LLM call and return the text response.

    Args:
        system: System prompt string.
        user: User message string.
        skill: Skill name used in log messages.

    Returns:
        Model response text, or a budget-exceeded message.
    """
    # Enforce session token budget
    used = st.session_state.get(_KEY_TOKENS, 0)
    if used >= SESSION_TOKEN_BUDGET:
        logger.warning(
            f"[{skill}] Session budget exceeded ({used:,}/{SESSION_TOKEN_BUDGET:,} tokens)."
        )
        return (
            f"⚠️ Session token budget exceeded "
            f"({used:,} / {SESSION_TOKEN_BUDGET:,} tokens used). "
            "Please refresh the page to start a new session."
        )

    logger.info(f"[{skill}] LLM call — model={OPENAI_MODEL}, temp={LLM_TEMPERATURE}")

    response = _client().invoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )
    content: str = response.content.strip()

    # Extract token counts
    prompt_tokens, completion_tokens = _extract_tokens(response)
    total = prompt_tokens + completion_tokens
    cost = (
        prompt_tokens / 1_000_000 * COST_PER_M_INPUT
        + completion_tokens / 1_000_000 * COST_PER_M_OUTPUT
    )

    logger.info(
        f"[{skill}] tokens — prompt={prompt_tokens}, completion={completion_tokens}, "
        f"total={total}, cost=${cost:.5f}"
    )

    # Accumulate in session state
    st.session_state[_KEY_TOKENS] = st.session_state.get(_KEY_TOKENS, 0) + total
    st.session_state[_KEY_COST] = st.session_state.get(_KEY_COST, 0.0) + cost
    st.session_state[_KEY_CALLS] = st.session_state.get(_KEY_CALLS, 0) + 1

    return content


def get_session_usage() -> dict:
    """Return current session token/cost stats from st.session_state."""
    return {
        "tokens": st.session_state.get(_KEY_TOKENS, 0),
        "cost": st.session_state.get(_KEY_COST, 0.0),
        "calls": st.session_state.get(_KEY_CALLS, 0),
    }


def _extract_tokens(response) -> tuple[int, int]:
    """Extract (prompt_tokens, completion_tokens) from an LLM response."""
    meta = getattr(response, "usage_metadata", None)
    if meta:
        return (
            getattr(meta, "input_tokens", 0),
            getattr(meta, "output_tokens", 0),
        )
    rm = getattr(response, "response_metadata", {}) or {}
    tu = rm.get("token_usage", {})
    return tu.get("prompt_tokens", 0), tu.get("completion_tokens", 0)
