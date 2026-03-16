"""Schemas for product CRUD endpoints.

Products are business-scoped — each product is an independent AI agent deployment.
"""

from pydantic import BaseModel, field_validator
from typing import Optional


class CreateProductRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    website_url: Optional[str] = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Product name cannot be empty")
        return v


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Product name cannot be empty")
        return v
