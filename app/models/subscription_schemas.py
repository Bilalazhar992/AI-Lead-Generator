"""Schemas for subscription plan management endpoints.

Enum fields use `Literal` types for Pydantic validation at request time.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, Literal


class ChangePlanRequest(BaseModel):
    plan_id: str
    billing_cycle: Literal["monthly", "annual"] = "monthly"


class CreatePlanRequest(BaseModel):
    name: str
    slug: str
    price_monthly_pkr: float
    price_annual_pkr: float
    max_products: int
    max_leads_per_month: int
    max_ai_messages_per_month: int
    max_team_members: int
    whatsapp_enabled: bool = False
    widget_enabled: bool = True
    remove_branding: bool = False
    is_active: bool = True
    display_order: int = 0

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Slug cannot be empty")
        if " " in v:
            raise ValueError("Slug must not contain spaces — use hyphens")
        return v

    @field_validator("price_monthly_pkr", "price_annual_pkr")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("max_products", "max_leads_per_month", "max_ai_messages_per_month", "max_team_members")
    @classmethod
    def limit_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Limit must be at least 1")
        return v


class UpdatePlanRequest(BaseModel):
    name: Optional[str] = None
    price_monthly_pkr: Optional[float] = None
    price_annual_pkr: Optional[float] = None
    max_products: Optional[int] = None
    max_leads_per_month: Optional[int] = None
    max_ai_messages_per_month: Optional[int] = None
    max_team_members: Optional[int] = None
    whatsapp_enabled: Optional[bool] = None
    widget_enabled: Optional[bool] = None
    remove_branding: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

    @field_validator("price_monthly_pkr", "price_annual_pkr")
    @classmethod
    def price_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("max_products", "max_leads_per_month", "max_ai_messages_per_month", "max_team_members")
    @classmethod
    def limit_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("Limit must be at least 1")
        return v
