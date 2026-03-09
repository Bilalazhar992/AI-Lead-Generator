from pydantic import BaseModel, EmailStr
from typing import Optional


class BusinessOnboardRequest(BaseModel):
    business_name: str
    business_type: str
    contact_email: EmailStr
    contact_phone: str
    timezone: str = "UTC"
    # Optional user_details enrichment
    company_website: Optional[str] = None
    industry: Optional[str] = None
    business_size: Optional[str] = None


class BusinessUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = None
    logo_url: Optional[str] = None
