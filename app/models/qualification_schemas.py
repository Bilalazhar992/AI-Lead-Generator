"""Schemas for qualification flow endpoints (per-product lead scoring).

Each product gets one qualification_flow document that defines the
qualifying questions, scoring thresholds, and actions per temperature level.
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal


class QuestionOption(BaseModel):
    label: str
    score: float


class QualificationQuestion(BaseModel):
    id: str
    question_text: str
    type: Literal["single_choice", "multiple_choice", "text", "number"]
    options: List[QuestionOption] = []
    text_score_default: Optional[float] = None
    is_required: bool = False
    display_order: int = 0

    @field_validator("options")
    @classmethod
    def options_required_for_choice(cls, v, info):
        q_type = info.data.get("type")
        if q_type in ("single_choice", "multiple_choice") and not v:
            raise ValueError(
                "Options are required for single_choice / multiple_choice questions"
            )
        return v


class CreateQualificationFlowRequest(BaseModel):
    is_enabled: bool = True
    trigger_type: Literal["after_greeting", "when_interested", "always"]
    trigger_keywords: List[str] = []
    questions: List[QualificationQuestion]
    hot_threshold: float
    warm_threshold: float
    hot_lead_action: Literal["book_meeting", "notify_team", "both"]
    warm_lead_action: Literal["book_meeting", "notify_team", "both"]
    cold_lead_action: Literal["book_meeting", "notify_team", "both"]

    @field_validator("questions")
    @classmethod
    def at_least_one_question(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one qualification question is required")
        return v

    @field_validator("warm_threshold")
    @classmethod
    def warm_below_hot(cls, v, info):
        hot = info.data.get("hot_threshold")
        if hot is not None and v >= hot:
            raise ValueError("warm_threshold must be less than hot_threshold")
        return v


class UpdateQualificationFlowRequest(BaseModel):
    is_enabled: Optional[bool] = None
    trigger_type: Optional[Literal["after_greeting", "when_interested", "always"]] = None
    trigger_keywords: Optional[List[str]] = None
    questions: Optional[List[QualificationQuestion]] = None
    hot_threshold: Optional[float] = None
    warm_threshold: Optional[float] = None
    hot_lead_action: Optional[Literal["book_meeting", "notify_team", "both"]] = None
    warm_lead_action: Optional[Literal["book_meeting", "notify_team", "both"]] = None
    cold_lead_action: Optional[Literal["book_meeting", "notify_team", "both"]] = None

    @field_validator("questions")
    @classmethod
    def at_least_one_question(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("At least one qualification question is required")
        return v
