from pydantic import BaseModel, Field
from typing import Optional


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = None


class UpdateProductRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = None
    status: Optional[str] = None
