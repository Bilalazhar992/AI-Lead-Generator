"""Routes for business staff management (business_owner only).

URL pattern: /api/businesses/{business_id}/staff/invite

The {business_id} path parameter explicitly identifies which business the
staff member is being invited to. The service layer verifies the caller
owns that business before proceeding.

Security layers:
  Layer 1 — require_role(BUSINESS_OWNER) → get_current_user() validates JWT +
             checks token type + verifies jti not blacklisted.
  Layer 2 — require_role() rejects any token whose role != BUSINESS_OWNER.
  Layer 3 — service layer verifies the owner owns the given business_id.
  Layer 4 — subscription team-limit check against the plan of that business.
"""

from fastapi import APIRouter, Depends
from app.controllers.business_staff_controller import BusinessStaffController
from app.models.staff_schemas import (
    InviteBusinessStaffRequest,
    UpdateBusinessStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)
from app.utils.auth_dependency import require_role
from app.utils.business_dependency import require_business_permission
from app.utils.constants import ROLES, PERMISSIONS

router = APIRouter(prefix="/api/businesses", tags=["Business Staff"])
_controller = BusinessStaffController()


@router.post("/{business_id}/staff/invite", status_code=201)
async def invite_business_staff(
    business_id: str,
    data: InviteBusinessStaffRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """
    Invite a new business staff member to a specific business.
    The signed-in owner must own the target business.
    """
    return await _controller.invite(data, current_user["sub"], business_id)


@router.get("/{business_id}/staff")
async def list_business_staff(
    business_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_TEAM)),
):
    """
    List all staff members of a business.
      - business_owner: always has access.
      - business_staff: requires manage_team permission.
    """
    return await _controller.list_staff(biz)


@router.patch("/{business_id}/staff/{user_id}/permissions")
async def update_staff_permissions(
    business_id: str,
    user_id: str,
    data: UpdateBusinessStaffPermissionsRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_TEAM)),
):
    """
    Replace a business staff member's permission set.
    The staff member must belong to this business.
    """
    return await _controller.update_permissions(user_id, data, biz)


@router.patch("/{business_id}/staff/{user_id}/status")
async def update_staff_status(
    business_id: str,
    user_id: str,
    data: UpdateStaffStatusRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_TEAM)),
):
    """
    Activate or deactivate a business staff account.
    The staff member must belong to this business.
    """
    return await _controller.update_status(user_id, data, biz)
