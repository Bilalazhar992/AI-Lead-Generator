"""Schemas for staff invitation and management endpoints.

Enum fields use `Literal` types so that Pydantic validates the exact set of
allowed values at request time and FastAPI auto-generates clear API docs.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Literal


# ── Platform Staff (created by super_admin) ──────────────────────────────────

class InvitePlatformStaffRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    permissions: List[
        Literal[
            "manage_subscriptions",
            "manage_ai_templates",
            "manage_businesses",
            "manage_platform_users",
            "view_analytics",
        ]
    ]
    department: Literal["support", "billing", "technical"]

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("permissions")
    @classmethod
    def at_least_one(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one permission is required")
        return v


class UpdatePlatformStaffPermissionsRequest(BaseModel):
    permissions: List[
        Literal[
            "manage_subscriptions",
            "manage_ai_templates",
            "manage_businesses",
            "manage_platform_users",
            "view_analytics",
        ]
    ]

    @field_validator("permissions")
    @classmethod
    def not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Permissions list cannot be empty")
        return v


# ── Business Staff (created by business_owner) ───────────────────────────────

class InviteBusinessStaffRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    permissions: List[
        Literal[
            "manage_products",
            "manage_leads",
            "manage_team",
            "manage_billing",
            "view_analytics",
        ]
    ]

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("permissions")
    @classmethod
    def at_least_one(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one permission is required")
        return v


class UpdateBusinessStaffPermissionsRequest(BaseModel):
    permissions: List[
        Literal[
            "manage_products",
            "manage_leads",
            "manage_team",
            "manage_billing",
            "view_analytics",
        ]
    ]

    @field_validator("permissions")
    @classmethod
    def not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Permissions list cannot be empty")
        return v


# ── Shared ────────────────────────────────────────────────────────────────────

class UpdateStaffStatusRequest(BaseModel):
    """Used to activate or deactivate any staff account."""
    is_active: bool
