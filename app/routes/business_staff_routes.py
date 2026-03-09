"""Routes for business staff management (business_owner only)."""

from fastapi import APIRouter, Depends
from app.controllers.business_staff_controller import BusinessStaffController
from app.models.staff_schemas import InviteBusinessStaffRequest
from app.utils.auth_dependency import require_role
from app.utils.constants import ROLES

# Security layers:
#   Layer 1 — require_role(BUSINESS_OWNER) → get_current_user() validates JWT +
#             checks token type + verifies jti not blacklisted.
#   Layer 2 — require_role() rejects any token whose role != BUSINESS_OWNER.
#   Layer 3 — service layer resolves business from owner_user_id, rejects if
#             the owner has not completed onboarding.

router = APIRouter(prefix="/api/staff", tags=["Business Staff"])
_controller = BusinessStaffController()


@router.post("/invite", status_code=201)
async def invite_business_staff(
    data: InviteBusinessStaffRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Invite a new business staff member (business_owner only)."""
    return await _controller.invite(data, current_user["sub"])
