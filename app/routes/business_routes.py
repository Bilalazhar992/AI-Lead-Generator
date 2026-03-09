from fastapi import APIRouter, Depends
from app.controllers.business_controller import BusinessController
from app.models.business_schemas import BusinessOnboardRequest, BusinessUpdateRequest
from app.utils.auth_dependency import require_role
from app.utils.constants import ROLES

# Security layers applied to every route in this file:
#   Layer 1 — require_role() calls get_current_user() which:
#              validates JWT signature, checks token type="access",
#              and verifies the jti is not blacklisted (signed out).
#   Layer 2 — require_role() rejects any token whose role != BUSINESS_OWNER.
#   Layer 3 — service layer asserts business.owner_user_id == current_user["sub"].
#   Layer 4 — DB write uses compound filter { _id, owner_user_id } so even a
#              direct DB call cannot mutate another owner's document.

router = APIRouter(prefix="/api/business", tags=["Business"])
_controller = BusinessController()


@router.post("/onboard", status_code=201)
async def onboard(
    data: BusinessOnboardRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Create the business profile for the signed-in business owner and seed a trial subscription."""
    return await _controller.onboard(data, current_user["sub"])


@router.get("/me")
async def get_my_business(
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Get the signed-in owner's business profile and active subscription."""
    return await _controller.get_my_business(current_user["sub"])


@router.put("/me")
async def update_my_business(
    data: BusinessUpdateRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Update business profile details."""
    return await _controller.update_my_business(data, current_user["sub"])
