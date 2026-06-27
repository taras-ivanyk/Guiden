"""Cycling coach skills package — one module per skill."""
from src.skills.analysis import analysis_skill
from src.skills.weather_skill import weather_skill
from src.skills.questions import question_skill
from src.skills.coaching import coaching_skill
from src.skills.next_session import next_session_skill
from src.skills.training_plan import training_plan_skill
from src.skills.expand_session import expand_session_skill
from src.skills.race_prep import race_prep_skill, expand_race_section_skill

__all__ = [
    "analysis_skill",
    "weather_skill",
    "question_skill",
    "coaching_skill",
    "next_session_skill",
    "training_plan_skill",
    "expand_session_skill",
    "race_prep_skill",
    "expand_race_section_skill",
]
