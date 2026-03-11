"""Schemas for AI template management endpoints.

AI Templates are platform-level resources managed by super_admin / platform_staff.
Business owners select a template when configuring their product's agent.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal


class TemplateQuestionOption(BaseModel):
    label: str
    score: float


class TemplateSuggestedQuestion(BaseModel):
    question_text: str
    type: Literal["single_choice", "text"]
    options: List[TemplateQuestionOption] = []
    is_required: bool = False


class CreateTemplateRequest(BaseModel):
    template_id: str = Field(..., example="real_estate_agent")
    name: str
    description: str
    icon: Optional[str] = None
    system_prompt_template: str
    default_tone: Literal["friendly", "professional", "casual"]
    default_personality_traits: List[str] = []
    default_primary_goal: Literal["book_meeting", "capture_lead"]
    default_greeting_message: str
    default_fallback_message: str
    default_meeting_cta_message: Optional[str] = None
    default_avoid_topics: List[str] = []
    default_handoff_keywords: List[str] = []
    suggested_questions: List[TemplateSuggestedQuestion] = []
    is_active: bool = True

    @field_validator("template_id")
    @classmethod
    def template_id_format(cls, v: str) -> str:
        v = v.strip().lower().replace(" ", "_")
        if not v:
            raise ValueError("template_id cannot be empty")
        return v


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    system_prompt_template: Optional[str] = None
    default_tone: Optional[Literal["friendly", "professional", "casual"]] = None
    default_personality_traits: Optional[List[str]] = None
    default_primary_goal: Optional[Literal["book_meeting", "capture_lead"]] = None
    default_greeting_message: Optional[str] = None
    default_fallback_message: Optional[str] = None
    default_meeting_cta_message: Optional[str] = None
    default_avoid_topics: Optional[List[str]] = None
    default_handoff_keywords: Optional[List[str]] = None
    suggested_questions: Optional[List[TemplateSuggestedQuestion]] = None
    is_active: Optional[bool] = None
