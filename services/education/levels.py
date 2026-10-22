from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final, Mapping, Optional, Sequence, Tuple


class StrEnum(str, Enum):
    """String enum compatibility for Python < 3.11."""
    def __str__(self) -> str:
        return str(self.value)


class Stage(StrEnum):
    EARLY_YEARS = "early_years"
    PRIMARY = "primary"
    JUNIOR_SECONDARY = "junior_secondary"
    SENIOR_SECONDARY = "senior_secondary"
    DIPLOMA = "diploma"
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    DOCTORAL = "doctoral"
    PROFESSIONAL = "professional"


class EducationLevelCode(StrEnum):
    # Early Years
    KG_1 = "kg_1"
    KG_2 = "kg_2"

    # Primary (Class 1-6 / Grade 1-6)
    PRIMARY_1 = "primary_1"
    PRIMARY_2 = "primary_2"
    PRIMARY_3 = "primary_3"
    PRIMARY_4 = "primary_4"
    PRIMARY_5 = "primary_5"
    PRIMARY_6 = "primary_6"

    # Junior Secondary (JSS 1-3 / Grade 7-9)
    JSS_1 = "jss_1"
    JSS_2 = "jss_2"
    JSS_3 = "jss_3"

    # Senior Secondary (SSS 1-3 / Grade 10-12)
    SSS_1 = "sss_1"
    SSS_2 = "sss_2"
    SSS_3 = "sss_3"

    # Diploma / TVET / Polytechnic
    DIPLOMA_1 = "diploma_1"
    DIPLOMA_2 = "diploma_2"
    ADVANCED_DIPLOMA = "advanced_diploma"

    # Undergraduate (Years 1-4 / Level 100-400)
    UG_1 = "ug_1"
    UG_2 = "ug_2"
    UG_3 = "ug_3"
    UG_4 = "ug_4"

    # Postgraduate
    PG_DIPLOMA = "pg_diploma"
    MASTERS = "masters"

    # Doctoral
    PHD = "phd"
    POSTDOC = "postdoc"

    # Professional
    PROFESSIONAL = "professional"


@dataclass(frozen=True, slots=True)
class EducationLevel:
    code: str
    label: str
    stage: Stage
    ordinal: int
    typical_age: Optional[Tuple[int, int]] = None
    description: str = ""
    max_choices: int = 4
    allowed_qtypes: Tuple[str, ...] = ("mcq", "true_false", "short_answer")


LEVELS: Final[Tuple[EducationLevel, ...]] = (
    # Early Years
    EducationLevel(
        code=EducationLevelCode.KG_1.value,
        label="Kindergarten 1 (KG 1)",
        stage=Stage.EARLY_YEARS,
        ordinal=0,
        typical_age=(4, 5),
        description="Early literacy, basic shapes, numbers, and foundational observations.",
        max_choices=3,
        allowed_qtypes=("mcq", "true_false"),
    ),
    EducationLevel(
        code=EducationLevelCode.KG_2.value,
        label="Kindergarten 2 (KG 2)",
        stage=Stage.EARLY_YEARS,
        ordinal=1,
        typical_age=(5, 6),
        description="Pre-primary reading readiness, counting, and everyday object classification.",
        max_choices=3,
        allowed_qtypes=("mcq", "true_false"),
    ),

    # Primary (Class 1 to 6)
    EducationLevel(
        code=EducationLevelCode.PRIMARY_1.value,
        label="Primary 1 / Grade 1",
        stage=Stage.PRIMARY,
        ordinal=2,
        typical_age=(6, 7),
        description="Introductory literacy, single-step arithmetic, visual and concrete concepts.",
        max_choices=3,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.PRIMARY_2.value,
        label="Primary 2 / Grade 2",
        stage=Stage.PRIMARY,
        ordinal=3,
        typical_age=(7, 8),
        description="Early reading comprehension, simple addition/subtraction, living things.",
        max_choices=3,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.PRIMARY_3.value,
        label="Primary 3 / Grade 3",
        stage=Stage.PRIMARY,
        ordinal=4,
        typical_age=(8, 9),
        description="Reading simple passages, multiplication facts, practical life science.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.PRIMARY_4.value,
        label="Primary 4 / Grade 4",
        stage=Stage.PRIMARY,
        ordinal=5,
        typical_age=(9, 10),
        description="Descriptive reading, multi-step word problems, earth and environment.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.PRIMARY_5.value,
        label="Primary 5 / Grade 5",
        stage=Stage.PRIMARY,
        ordinal=6,
        typical_age=(10, 11),
        description="Paragraph inference, fractions and decimals, basic systems and society.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.PRIMARY_6.value,
        label="Primary 6 / Grade 6",
        stage=Stage.PRIMARY,
        ordinal=7,
        typical_age=(11, 12),
        description="Primary exit level, critical reading, pre-algebra concepts, integrated science.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Junior Secondary / Middle School (Grades 7 - 9)
    EducationLevel(
        code=EducationLevelCode.JSS_1.value,
        label="Junior Secondary 1 / Grade 7",
        stage=Stage.JUNIOR_SECONDARY,
        ordinal=8,
        typical_age=(12, 13),
        description="Transition to departmentalized science, introductory algebra, textual analysis.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.JSS_2.value,
        label="Junior Secondary 2 / Grade 8",
        stage=Stage.JUNIOR_SECONDARY,
        ordinal=9,
        typical_age=(13, 14),
        description="Intermediate middle-school curriculum, geometry, scientific inquiry.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.JSS_3.value,
        label="Junior Secondary 3 / Grade 9",
        stage=Stage.JUNIOR_SECONDARY,
        ordinal=10,
        typical_age=(14, 15),
        description="Basic Education Certificate / High-school prep, comprehensive science and math.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Senior Secondary / High School (Grades 10 - 12)
    EducationLevel(
        code=EducationLevelCode.SSS_1.value,
        label="Senior Secondary 1 / Grade 10",
        stage=Stage.SENIOR_SECONDARY,
        ordinal=11,
        typical_age=(15, 16),
        description="High school foundational curriculum, specialized sciences, literature, algebra II.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.SSS_2.value,
        label="Senior Secondary 2 / Grade 11",
        stage=Stage.SENIOR_SECONDARY,
        ordinal=12,
        typical_age=(16, 17),
        description="Advanced high school, college prep, pre-calculus, specialized chemistry/physics/humanities.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.SSS_3.value,
        label="Senior Secondary 3 / Grade 12",
        stage=Stage.SENIOR_SECONDARY,
        ordinal=13,
        typical_age=(17, 18),
        description="WASSCE / SAT / A-Level / IB diploma exit exams, rigorous summative assessments.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Diploma / TVET / Polytechnic (Post-secondary applied credentials)
    EducationLevel(
        code=EducationLevelCode.DIPLOMA_1.value,
        label="Diploma Year 1 / National Diploma (ND 1)",
        stage=Stage.DIPLOMA,
        ordinal=14,
        typical_age=(18, 19),
        description="First-year polytechnic, technical college, or TVET curriculum emphasizing applied fundamentals and practical techniques.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.DIPLOMA_2.value,
        label="Diploma Year 2 / National Diploma (ND 2)",
        stage=Stage.DIPLOMA,
        ordinal=15,
        typical_age=(19, 20),
        description="Second-year polytechnic/vocational diploma, specialized laboratory techniques, field diagnostics, and intermediate project execution.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.ADVANCED_DIPLOMA.value,
        label="Higher National Diploma (HND) / Advanced Diploma",
        stage=Stage.DIPLOMA,
        ordinal=16,
        typical_age=(20, 22),
        description="Advanced technical institute credential, applied engineering/management theory, supervisory protocols, and industrial problem solving.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Undergraduate (Years 1 - 4)
    EducationLevel(
        code=EducationLevelCode.UG_1.value,
        label="Undergraduate Year 1 / Level 100",
        stage=Stage.UNDERGRADUATE,
        ordinal=17,
        typical_age=(18, 19),
        description="First-year university survey courses, foundational discipline theories and methods.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.UG_2.value,
        label="Undergraduate Year 2 / Level 200",
        stage=Stage.UNDERGRADUATE,
        ordinal=18,
        typical_age=(19, 20),
        description="Intermediate major coursework, lab analysis, analytical problem solving.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.UG_3.value,
        label="Undergraduate Year 3 / Level 300",
        stage=Stage.UNDERGRADUATE,
        ordinal=19,
        typical_age=(20, 21),
        description="Advanced undergraduate seminar, domain-specific models, case studies.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.UG_4.value,
        label="Undergraduate Year 4 / Level 400",
        stage=Stage.UNDERGRADUATE,
        ordinal=20,
        typical_age=(21, 22),
        description="Senior capstone, thesis research, complex multi-step domain evaluation.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Postgraduate
    EducationLevel(
        code=EducationLevelCode.PG_DIPLOMA.value,
        label="Postgraduate Diploma",
        stage=Stage.POSTGRADUATE,
        ordinal=21,
        typical_age=None,
        description="Applied post-baccalaureate credential, professional conversion.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.MASTERS.value,
        label="Master's Degree (MSc / MA / MBA)",
        stage=Stage.POSTGRADUATE,
        ordinal=22,
        typical_age=None,
        description="Graduate-level inquiry, theoretical synthesis, research methodology, advanced critique.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Doctoral
    EducationLevel(
        code=EducationLevelCode.PHD.value,
        label="Doctoral / PhD",
        stage=Stage.DOCTORAL,
        ordinal=23,
        typical_age=None,
        description="Frontier academic inquiry, epistemological critique, original research defence, high-rigor peer review level.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
    EducationLevel(
        code=EducationLevelCode.POSTDOC.value,
        label="Postdoctoral / Advanced Fellowship",
        stage=Stage.DOCTORAL,
        ordinal=24,
        typical_age=None,
        description="Specialized frontier research, cross-disciplinary synthesis, scientific critique.",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),

    # Professional
    EducationLevel(
        code=EducationLevelCode.PROFESSIONAL.value,
        label="Professional Certification",
        stage=Stage.PROFESSIONAL,
        ordinal=25,
        typical_age=None,
        description="Industry board certification, professional licensing (CPA, Bar, Medical, Project Management).",
        max_choices=4,
        allowed_qtypes=("mcq", "true_false", "short_answer"),
    ),
)

LEVELS_BY_CODE: Final[Mapping[str, EducationLevel]] = MappingProxyType(
    {level.code: level for level in LEVELS}
)

DEFAULT_LEVEL_CODE: Final[str] = EducationLevelCode.PRIMARY_1.value  # Primary 1 / Grade 1 default


def get_level(code_or_name: Optional[str]) -> Optional[EducationLevel]:
    """Retrieve an EducationLevel by its exact code or alias."""
    if not code_or_name:
        return None
    cleaned = str(code_or_name).strip().lower()
    if cleaned in LEVELS_BY_CODE:
        return LEVELS_BY_CODE[cleaned]
    from .aliases import LEVEL_ALIASES
    if cleaned in LEVEL_ALIASES:
        return LEVELS_BY_CODE.get(LEVEL_ALIASES[cleaned])
    return None


def list_levels() -> Sequence[EducationLevel]:
    """Return all defined education levels in ordinal sequence."""
    return LEVELS


def levels_by_stage(stage: Stage | str) -> Sequence[EducationLevel]:
    """Return all education levels matching a given stage."""
    target_stage = stage.value if isinstance(stage, Stage) else str(stage)
    return tuple(l for l in LEVELS if l.stage.value == target_stage)


def codes_in_range(min_code: Optional[str] = None, max_code: Optional[str] = None) -> Sequence[str]:
    """Return a sequence of level codes bounded between min_code and max_code (inclusive)."""
    min_ord = LEVELS_BY_CODE[min_code].ordinal if min_code and min_code in LEVELS_BY_CODE else 0
    max_ord = (
        LEVELS_BY_CODE[max_code].ordinal
        if max_code and max_code in LEVELS_BY_CODE
        else max(l.ordinal for l in LEVELS)
    )
    if min_ord > max_ord:
        min_ord, max_ord = max_ord, min_ord
    return tuple(l.code for l in LEVELS if min_ord <= l.ordinal <= max_ord)
