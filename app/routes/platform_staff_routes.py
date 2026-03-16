"""Routes for platform staff management.

All routes require MANAGE_PLATFORM_USERS permission.
super_admin has it by default; platform_staff can be assigned it at invite time.

Routes:
  POST  /api/platform-staff/invite                        → invite new platform staff
  GET   /api/platform-staff                               → list all platform staff
  PATCH /api/platform-staff/{user_id}/permissions         → replace permissions
  PATCH /api/platform-staff/{user_id}/status              → activate / deactivate
"""

from fastapi import APIRouter, Depends
from app.controllers.platform_staff_controller import PlatformStaffController
from app.models.staff_schemas import (
    InvitePlatformStaffRequest,
    UpdatePlatformStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)
from app.utils.auth_dependency import require_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(prefix="/api/platform-staff", tags=["Platform Staff"])
_controller = PlatformStaffController()


@router.post("/invite", status_code=201)
async def invite_platform_staff(
    data: InvitePlatformStaffRequest,
    _: dict = Depends(require_permission(PERMISSIONS.MANAGE_PLATFORM_USERS)),
):
    """Invite a new platform staff member."""
    return await _controller.invite(data)


@router.get("")
async def list_platform_staff(
    _: dict = Depends(require_permission(PERMISSIONS.MANAGE_PLATFORM_USERS)),
):
    """List all platform staff members."""
    return await _controller.list_staff()


@router.patch("/{user_id}/permissions")
async def update_permissions(
    user_id: str,
    data: UpdatePlatformStaffPermissionsRequest,
    _: dict = Depends(require_permission(PERMISSIONS.MANAGE_PLATFORM_USERS)),
):
    """Replace a platform staff member's permission set."""
    return await _controller.update_permissions(user_id, data)


@router.patch("/{user_id}/status")
async def update_status(
    user_id: str,
    data: UpdateStaffStatusRequest,
    _: dict = Depends(require_permission(PERMISSIONS.MANAGE_PLATFORM_USERS)),
):
    """Activate or deactivate a platform staff account."""
    return await _controller.update_status(user_id, data)
