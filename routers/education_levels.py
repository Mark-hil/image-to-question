"""
API router for education levels catalog and resolution.
Serves standardized taxonomy covering Kindergarten through PhD.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Response, Query
from pydantic import BaseModel, Field

from services.education.levels import (
    Stage,
    LEVELS,
    DEFAULT_LEVEL_CODE,
    get_level,
    list_levels,
    levels_by_stage,
)
from services.education.resolver import resolve_level_and_label

router = APIRouter(prefix="/education-levels", tags=["Education Levels"])


class EducationLevelDTO(BaseModel):
    code: str
    label: str
    stage: str
    ordinal: int
    typical_age: Optional[List[int]] = None
    description: str
    max_choices: int
    allowed_qtypes: List[str]


class StageDTO(BaseModel):
    code: str
    label: str
    description: str


STAGE_METADATA = [
    StageDTO(code=Stage.EARLY_YEARS.value, label="Early Years / Kindergarten", description="Nursery and Kindergarten (Ages 4-6)"),
    StageDTO(code=Stage.PRIMARY.value, label="Primary / Elementary School", description="Basic / Grades 1 to 6 (Ages 6-12)"),
    StageDTO(code=Stage.JUNIOR_SECONDARY.value, label="Junior Secondary / Middle School", description="JHS / Basic 7-9 / Grades 7 to 9 (Ages 12-15)"),
    StageDTO(code=Stage.SENIOR_SECONDARY.value, label="Senior Secondary / High School", description="SHS / SSS / Grades 10 to 12 / A-Levels (Ages 15-18)"),
    StageDTO(code=Stage.DIPLOMA.value, label="Diploma / TVET / Polytechnic", description="National Diploma (ND 1-2), Higher National Diploma (HND), Associate Degrees"),
    StageDTO(code=Stage.UNDERGRADUATE.value, label="Undergraduate / Tertiary", description="University Years 1 to 4 / Level 100 to 400"),
    StageDTO(code=Stage.POSTGRADUATE.value, label="Postgraduate", description="Postgraduate Diplomas, Master's (MSc, MA, MBA)"),
    StageDTO(code=Stage.DOCTORAL.value, label="Doctoral / Advanced Research", description="PhD, Doctorate, Postdoctoral Fellowships"),
    StageDTO(code=Stage.PROFESSIONAL.value, label="Professional Certification", description="Licensing, Board Exams, Industry Certifications"),
]


@router.get("", summary="Get Education Levels Catalog")
async def get_education_levels(response: Response) -> Dict[str, Any]:
    """
    Retrieve all supported educational levels from Kindergarten/Primary 1 to PhD.
    Cached for client efficiency (24 hour public cache).
    """
    response.headers["Cache-Control"] = "public, max-age=86400"

    dto_list = [
        EducationLevelDTO(
            code=lvl.code,
            label=lvl.label,
            stage=lvl.stage.value,
            ordinal=lvl.ordinal,
            typical_age=list(lvl.typical_age) if lvl.typical_age else None,
            description=lvl.description,
            max_choices=lvl.max_choices,
            allowed_qtypes=list(lvl.allowed_qtypes),
        ).model_dump()
        for lvl in list_levels()
    ]

    return {
        "status": "success",
        "default_level": DEFAULT_LEVEL_CODE,
        "total_levels": len(dto_list),
        "stages": [s.model_dump() for s in STAGE_METADATA],
        "levels": dto_list,
    }


@router.get("/resolve", summary="Resolve Freeform String to Canonical Level")
async def resolve_education_level(
    query: str = Query(..., description="Raw text e.g. 'Grade 5', 'Class 5A', 'Level 300', 'PhD'")
) -> Dict[str, Any]:
    """
    Resolve any historical, regional, or informal grade identifier into a canonical EducationLevel.
    """
    level, label = resolve_level_and_label(query)
    level_dto = None
    if level:
        level_dto = EducationLevelDTO(
            code=level.code,
            label=level.label,
            stage=level.stage.value,
            ordinal=level.ordinal,
            typical_age=list(level.typical_age) if level.typical_age else None,
            description=level.description,
            max_choices=level.max_choices,
            allowed_qtypes=list(level.allowed_qtypes),
        ).model_dump()

    return {
        "status": "success",
        "query": query,
        "matched": level is not None,
        "level": level_dto,
        "resolved": level_dto,
        "class_label": label,
    }
