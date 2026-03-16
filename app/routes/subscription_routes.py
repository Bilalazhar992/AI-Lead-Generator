"""Business-scoped subscription routes.

Both endpoints require MANAGE_BILLING permission:
  - business_owner   → passes automatically (implicit full access)
  - business_staff   → must have manage_billing in their permissions list

URL pattern: /api/businesses/{business_id}/subscription[/change-plan]
The {business_id} path parameter is injected into get_business_context automatically,
which verifies ownership (owner) or membership (staff) before the handler runs.
"""

from fastapi import APIRouter, Depends
from app.controllers.subscription_controller import SubscriptionController
from app.models.subscription_schemas import ChangePlanRequest
from app.utils.business_dependency import require_business_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(prefix="/api/businesses", tags=["Subscriptions"])
_controller = SubscriptionController()


@router.get("/{business_id}/subscription")
async def get_subscription(
    business_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_BILLING)),
):
    """
    Get the active subscription and full change history for a business.
    Accessible to business_owner and business_staff with manage_billing permission.
    """
    return await _controller.get_subscription(biz)


@router.post("/{business_id}/subscription/cancel")
async def cancel_subscription(
    business_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_BILLING)),
):
    """
    Cancel the active subscription for a business.
    Archives the current subscription to history with change_event: "cancelled".
    Sets subscription status to "cancelled" — does not delete the record.
    """
    return await _controller.cancel_subscription(biz)


@router.post("/{business_id}/subscription/change-plan")
async def change_plan(
    business_id: str,
    data: ChangePlanRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_BILLING)),
):
    """
    Change the active subscription to a new plan.

    - Archives the current subscription snapshot to subscription_history.
    - Overwrites the active subscription with new plan details.
    - Resets usage counters (leads, messages, conversations) for the new period.
    - change_event is determined automatically:
        trialing → any paid plan  : "activated"
        new price > old price      : "upgraded"
        new price < old price      : "downgraded"
        same price / same plan     : "renewed"
    """
    return await _controller.change_plan(biz, data)
