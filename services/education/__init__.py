"""
Education package for multi-tiered educational level alignment (Primary 1 to PhD).
Provides standardized registry, resolution of historical class_id aliases, and
pedagogical prompt profiles for fine-tuned LLM question generation.
"""

from .levels import (
    Stage,
    EducationLevelCode,
    EducationLevel,
    LEVELS,
    LEVELS_BY_CODE,
    DEFAULT_LEVEL_CODE,
    get_level,
    list_levels,
    levels_by_stage,
    codes_in_range,
)
from .aliases import LEVEL_ALIASES
from .resolver import resolve_level, resolve_level_and_label
from .prompt_profiles import (
    PromptProfile,
    get_prompt_profile,
    PROMPT_PROFILES_BY_STAGE,
)

__all__ = [
    "Stage",
    "EducationLevelCode",
    "EducationLevel",
    "LEVELS",
    "LEVELS_BY_CODE",
    "DEFAULT_LEVEL_CODE",
    "get_level",
    "list_levels",
    "levels_by_stage",
    "codes_in_range",
    "LEVEL_ALIASES",
    "resolve_level",
    "resolve_level_and_label",
    "PromptProfile",
    "get_prompt_profile",
    "PROMPT_PROFILES_BY_STAGE",
]
