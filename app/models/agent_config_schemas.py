"""Schemas for agent configuration endpoints (per-product AI personality).

Flow:
  1. Business user selects a template_id → POST creates agent_config
     by replicating all template defaults into the config.
  2. Business user customises fields → PATCH updates individual fields.
"""

from pydantic import BaseModel
from typing import List, Optional, Literal


class SelectTemplateRequest(BaseModel):
    """Step 1: Select an AI template to initialise this product's agent config."""
    template_id: str


class UpdateAgentConfigRequest(BaseModel):
    """Step 2: Customise individual fields of the agent config."""
    template_id: Optional[str] = None
    company_name: Optional[str] = None
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    target_audience: Optional[str] = None
    pricing_info: Optional[str] = None
    tone: Optional[Literal["friendly", "professional", "casual"]] = None
    personality_traits: Optional[List[str]] = None
    primary_goal: Optional[Literal["book_meeting", "capture_lead", "answer_questions"]] = None
    greeting_message: Optional[str] = None
    fallback_message: Optional[str] = None
    meeting_cta_message: Optional[str] = None
    avoid_topics: Optional[List[str]] = None
    never_say: Optional[List[str]] = None
    always_include: Optional[List[str]] = None
    handoff_enabled: Optional[bool] = None
    handoff_keywords: Optional[List[str]] = None
    handoff_after_messages: Optional[int] = None
    handoff_message: Optional[str] = None
