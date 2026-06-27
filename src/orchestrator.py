"""LangGraph orchestrator for the AI Endurance Coach.

Two-phase design:
  Phase 1 — run_analysis_phase: analysis → weather → questions
  Phase 2 — run_coaching_phase: coaching (with user answers)

This lets the Streamlit UI pause between phases to collect user answers.
"""

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from src.profile import UserProfile
from src.skills import analysis_skill, weather_skill, question_skill, coaching_skill


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class CoachState(TypedDict):
    """Shared state flowing through the LangGraph nodes."""

    activity: dict
    profile: UserProfile
    analysis: Optional[dict]
    weather: Optional[dict]
    questions: Optional[list[str]]
    user_answers: Optional[dict[str, str]]
    final_output: Optional[str]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def _node_analysis(state: CoachState) -> CoachState:
    """Run analysis_skill and store result in state."""
    result = analysis_skill(state["activity"], state["profile"])
    return {**state, "analysis": result}


def _node_weather(state: CoachState) -> CoachState:
    """Run weather_skill and store result in state."""
    result = weather_skill(state["activity"])
    return {**state, "weather": result}


def _node_questions(state: CoachState) -> CoachState:
    """Run question_skill and store result in state."""
    questions = question_skill(state["activity"], state["analysis"])
    return {**state, "questions": questions}


def _node_coaching(state: CoachState) -> CoachState:
    """Run coaching_skill and store result in state."""
    result = coaching_skill(
        activity=state["activity"],
        profile=state["profile"],
        analysis=state["analysis"],
        weather=state["weather"],
        user_answers=state.get("user_answers") or {},
    )
    return {**state, "final_output": result}


# ---------------------------------------------------------------------------
# Graph builders
# ---------------------------------------------------------------------------

def _build_analysis_graph() -> StateGraph:
    """Build the Phase 1 graph: analysis → weather → questions."""
    graph = StateGraph(CoachState)

    graph.add_node("analysis", _node_analysis)
    graph.add_node("weather", _node_weather)
    graph.add_node("questions", _node_questions)

    graph.set_entry_point("analysis")
    graph.add_edge("analysis", "weather")
    graph.add_edge("weather", "questions")
    graph.add_edge("questions", END)

    return graph.compile()


def _build_coaching_graph() -> StateGraph:
    """Build the Phase 2 graph: coaching only."""
    graph = StateGraph(CoachState)

    graph.add_node("coaching", _node_coaching)

    graph.set_entry_point("coaching")
    graph.add_edge("coaching", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_analysis_phase(activity: dict, profile: UserProfile) -> CoachState:
    """Run Phase 1: analysis, weather, and clarifying questions.

    Args:
        activity: Full activity detail dict (from strava.get_activity_detail).
        profile: Athlete's UserProfile.

    Returns:
        Intermediate CoachState with analysis, weather, and questions populated.
    """
    initial_state: CoachState = {
        "activity": activity,
        "profile": profile,
        "analysis": None,
        "weather": None,
        "questions": None,
        "user_answers": None,
        "final_output": None,
    }

    graph = _build_analysis_graph()
    return graph.invoke(initial_state)


def run_coaching_phase(state: CoachState, user_answers: dict[str, str]) -> CoachState:
    """Run Phase 2: synthesize everything into a final coaching output.

    Args:
        state: Intermediate state returned by run_analysis_phase.
        user_answers: Dict mapping question strings to athlete's answers.

    Returns:
        Final CoachState with final_output populated.
    """
    updated_state = {**state, "user_answers": user_answers}

    graph = _build_coaching_graph()
    return graph.invoke(updated_state)
