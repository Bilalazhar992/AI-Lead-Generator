from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


class BusinessCreateRequest(BaseModel):
    business_name: str
    business_type: str
    contact_email: EmailStr
    contact_phone: str
    timezone: str = "UTC"
    website_url: Optional[str] = None
    industry: Optional[str] = None
    business_size: Optional[str] = None



class AdminBusinessStatusRequest(BaseModel):
    status: Literal["active", "suspended", "cancelled"]


class BusinessUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    business_size: Optional[str] = None
