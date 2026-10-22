"""
Resolver for translating freeform user strings or class identifiers into canonical EducationLevel objects.
Extracts canonical level codes and optional class room labels (e.g. 'Class 5A' -> primary_5, '5A').
"""

import re
from typing import Optional, Tuple
from .levels import EducationLevel, LEVELS_BY_CODE, get_level
from .aliases import LEVEL_ALIASES

# Regex patterns for fast extraction
_GRADE_NUM_RE = re.compile(
    r"\b(?:grade|class|basic|primary|year|p|g)\s*[-_]?\s*([1-9]|1[0-2])(?![0-9])",
    re.IGNORECASE,
)
_JHS_NUM_RE = re.compile(
    r"\b(?:jhs|jss|junior\s+secondary|junior\s+high)\s*[-_]?\s*([1-3])(?![0-9])",
    re.IGNORECASE,
)
_SHS_NUM_RE = re.compile(
    r"\b(?:shs|sss|senior\s+secondary|senior\s+high)\s*[-_]?\s*([1-3])(?![0-9])",
    re.IGNORECASE,
)
_LEVEL_NUM_RE = re.compile(
    r"\b(?:level\s*|ug\s*|year\s*)(100|200|300|400|[1-4])(?![0-9])",
    re.IGNORECASE,
)
_DIPLOMA_NUM_RE = re.compile(
    r"\b(?:diploma|deploma|nd|polytechnic)\s*[-_]?\s*([1-2])(?![0-9])",
    re.IGNORECASE,
)


def _clean_input(raw: str) -> str:
    cleaned = raw.strip().lower()
    # Replace multiple spaces/underscores/hyphens with single space
    cleaned = re.sub(r"[\s\-_]+", " ", cleaned)
    # Remove surrounding quotes or punctuation
    cleaned = cleaned.strip("\"'.,;:")
    return cleaned


def resolve_level(raw: Optional[str]) -> Optional[EducationLevel]:
    """
    Resolve a freeform string to an EducationLevel.
    
    Examples:
        resolve_level("primary_5") -> EducationLevel(code="primary_5")
        resolve_level("Grade 5") -> EducationLevel(code="primary_5")
        resolve_level("Class 5A") -> EducationLevel(code="primary_5")
        resolve_level("JHS 2") -> EducationLevel(code="jss_2")
        resolve_level("Level 300") -> EducationLevel(code="ug_3")
        resolve_level("PhD") -> EducationLevel(code="phd")
        resolve_level("5") -> EducationLevel(code="primary_5")
        resolve_level("10") -> EducationLevel(code="sss_1")
    """
    if not raw or not str(raw).strip():
        return None

    cleaned = _clean_input(str(raw))

    # 1. Direct code lookup
    if cleaned in LEVELS_BY_CODE:
        return LEVELS_BY_CODE[cleaned]

    # 2. Direct alias lookup
    if cleaned in LEVEL_ALIASES:
        target_code = LEVEL_ALIASES[cleaned]
        return LEVELS_BY_CODE.get(target_code)

    # 3. Check for standalone digits e.g. "1" - "12"
    if cleaned.isdigit():
        num = int(cleaned)
        if 1 <= num <= 6:
            return LEVELS_BY_CODE.get(f"primary_{num}")
        elif 7 <= num <= 9:
            return LEVELS_BY_CODE.get(f"jss_{num - 6}")
        elif 10 <= num <= 12:
            return LEVELS_BY_CODE.get(f"sss_{num - 9}")

    # 4. Regex matching for JHS/JSS
    jhs_match = _JHS_NUM_RE.search(cleaned)
    if jhs_match:
        digit = jhs_match.group(1)
        return LEVELS_BY_CODE.get(f"jss_{digit}")

    # 5. Regex matching for SHS/SSS
    shs_match = _SHS_NUM_RE.search(cleaned)
    if shs_match:
        digit = shs_match.group(1)
        return LEVELS_BY_CODE.get(f"sss_{digit}")

    # 6. Regex matching for Grade / Class / Basic 1-12
    grade_match = _GRADE_NUM_RE.search(cleaned)
    if grade_match:
        num = int(grade_match.group(1))
        if 1 <= num <= 6:
            return LEVELS_BY_CODE.get(f"primary_{num}")
        elif 7 <= num <= 9:
            return LEVELS_BY_CODE.get(f"jss_{num - 6}")
        elif 10 <= num <= 12:
            return LEVELS_BY_CODE.get(f"sss_{num - 9}")

    # 7. University level matching (100-400 or 1-4)
    lvl_match = _LEVEL_NUM_RE.search(cleaned)
    if lvl_match:
        val = lvl_match.group(1)
        lvl_map = {"100": "ug_1", "200": "ug_2", "300": "ug_3", "400": "ug_4",
                   "1": "ug_1", "2": "ug_2", "3": "ug_3", "4": "ug_4"}
        code = lvl_map.get(val)
        if code and code in LEVELS_BY_CODE:
            return LEVELS_BY_CODE[code]

    # 8. Diploma / ND level matching (1 or 2)
    dip_match = _DIPLOMA_NUM_RE.search(cleaned)
    if dip_match:
        digit = dip_match.group(1)
        return LEVELS_BY_CODE.get(f"diploma_{digit}")

    # 9. Check for keyword substrings
    if "hnd" in cleaned or "higher national diploma" in cleaned or "advanced diploma" in cleaned:
        return LEVELS_BY_CODE.get("advanced_diploma")
    if "diploma" in cleaned or "deploma" in cleaned or "polytechnic" in cleaned or "tvet" in cleaned or "national diploma" in cleaned:
        if "2" in cleaned or "two" in cleaned or "second" in cleaned:
            return LEVELS_BY_CODE.get("diploma_2")
        return LEVELS_BY_CODE.get("diploma_1")
    if "phd" in cleaned or "doctor" in cleaned or "dphil" in cleaned:
        return LEVELS_BY_CODE.get("phd")
    if "master" in cleaned or "msc" in cleaned or "mba" in cleaned or "mphil" in cleaned:
        return LEVELS_BY_CODE.get("masters")
    if "postdoc" in cleaned:
        return LEVELS_BY_CODE.get("postdoc")
    if "undergrad" in cleaned or "bachelor" in cleaned or "bsc" in cleaned:
        return LEVELS_BY_CODE.get("ug_1")
    if "nursery" in cleaned or "kg 1" in cleaned or "kg1" in cleaned:
        return LEVELS_BY_CODE.get("kg_1")
    if "kg 2" in cleaned or "kg2" in cleaned:
        return LEVELS_BY_CODE.get("kg_2")

    return None


def resolve_level_and_label(
    education_level: Optional[str] = None,
    class_id: Optional[str] = None,
    class_label: Optional[str] = None
) -> Tuple[Optional[EducationLevel], Optional[str]]:
    """
    Given combinations of education_level, legacy class_id, and class_label,
    resolves to (EducationLevel, class_label).
    Supports backward-compatibility with calling with a single argument (raw).
    """
    # 1. Resolve level: check education_level first, then class_id, then class_label
    level = None
    if education_level and str(education_level).strip():
        level = resolve_level(str(education_level))
    if not level and class_id and str(class_id).strip():
        level = resolve_level(str(class_id))
    if not level and class_label and str(class_label).strip():
        level = resolve_level(str(class_label))

    # 2. Determine class_label
    label = None
    if class_label and str(class_label).strip():
        label = str(class_label).strip()
    elif class_id and str(class_id).strip():
        label = str(class_id).strip()
    elif education_level and str(education_level).strip():
        cleaned_input = str(education_level).strip()
        if level and cleaned_input.lower() == level.code:
            label = level.label
        else:
            label = cleaned_input
    elif level:
        label = level.label

    return level, label
