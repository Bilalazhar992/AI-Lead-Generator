"""Platform admin CRM routes — read-only cross-tenant views.

All routes are guarded by require_permission(VIEW_ANALYTICS).
This single guard covers:
  - super_admin      → has VIEW_ANALYTICS in their default permissions
  - platform_staff   → when VIEW_ANALYTICS was assigned at invite time

No business_owner or business_staff can call these endpoints.

URL prefix: /api/admin/businesses
"""

from fastapi import APIRouter, Depends
from app.controllers.admin_controller import AdminController
from app.utils.auth_dependency import require_permission
from app.utils.constants import PERMISSIONS
from app.models.business_schemas import AdminBusinessStatusRequest


router = APIRouter(prefix="/api/admin/businesses", tags=["Admin CRM"])
_controller = AdminController()


@router.get("")
async def list_businesses(
    _: dict = Depends(require_permission(PERMISSIONS.VIEW_ANALYTICS)),
):
    """
    List all businesses on the platform with their active subscription summary.

    Returns for each business:
      - Full business profile
      - Subscription: plan_slug, status, billing_cycle, period_end,
        usage counters (leads, messages, conversations), limit flags
    """
    return await _controller.list_businesses()


@router.get("/{business_id}")
async def get_business(
    business_id: str,
    _: dict = Depends(require_permission(PERMISSIONS.VIEW_ANALYTICS)),
):
    """
    Get full detail of a single business including its active subscription.
    Returns 404 if the business does not exist.
    """
    return await _controller.get_business(business_id)


@router.get("/{business_id}/subscription")
async def get_business_subscription(
    business_id: str,
    _: dict = Depends(require_permission(PERMISSIONS.VIEW_ANALYTICS)),
):
    """
    Get the active subscription and full change history for a business.

    History is sorted newest-first so the most recent change_event is history[0].
    change_event values: activated | upgraded | downgraded | renewed | cancelled | past_due
    """
    return await _controller.get_business_subscription(business_id)


@router.get("/{business_id}/products")
async def get_business_products(
    business_id: str,
    _: dict = Depends(require_permission(PERMISSIONS.VIEW_ANALYTICS)),
):
    """
    List all products (AI agents) belonging to a business.
    Sorted newest-first.
    """
    return await _controller.get_business_products(business_id)


@router.get("/{business_id}/staff")
async def get_business_staff(
    business_id: str,
    _: dict = Depends(require_permission(PERMISSIONS.VIEW_ANALYTICS)),
):
    """
    List all staff members of a business.
    Returns user profile + permissions + joined_at for each member.
    """
    return await _controller.get_business_staff(business_id)




@router.patch("/{business_id}/status")
async def update_business_status(
    business_id: str,
    data: AdminBusinessStatusRequest,
    _: dict = Depends(require_permission(PERMISSIONS.MANAGE_BUSINESSES)),
):
    """
    Set a business status to active, suspended, or cancelled.
    Requires MANAGE_BUSINESSES permission (super_admin by default;
    assignable to platform_staff).
    """
    return await _controller.update_business_status(business_id, data)
