"""Routes for platform staff management (super_admin only)."""

from fastapi import APIRouter, Depends
from app.controllers.platform_staff_controller import PlatformStaffController
from app.models.staff_schemas import InvitePlatformStaffRequest
from app.utils.auth_dependency import require_role
from app.utils.constants import ROLES

# Security: require_role(SUPER_ADMIN) → only super admins can create platform staff.

router = APIRouter(prefix="/api/platform-staff", tags=["Platform Staff"])
_controller = PlatformStaffController()


@router.post("/invite", status_code=201)
async def invite_platform_staff(
    data: InvitePlatformStaffRequest,
    current_user: dict = Depends(require_role(ROLES.SUPER_ADMIN)),
):
    """Invite a new platform staff member (super_admin only)."""
    return await _controller.invite(data)
