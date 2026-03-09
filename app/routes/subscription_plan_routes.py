"""Routes for subscription plan management.

Admin routes (create, update, deactivate) are guarded by
`require_permission(MANAGE_SUBSCRIPTIONS)` — accessible to:
  - super_admin (has the permission by default)
  - platform_staff (if assigned the permission at invite time)

Public routes (list, get) require no authentication.
"""

from fastapi import APIRouter, Depends
from app.controllers.subscription_plan_controller import SubscriptionPlanController
from app.models.subscription_schemas import CreatePlanRequest, UpdatePlanRequest
from app.utils.auth_dependency import require_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(tags=["Subscription Plans"])
_controller = SubscriptionPlanController()


# ── Admin routes (permission-gated) ──────────────────────────────────────

@router.post("/api/admin/plans", status_code=201)
async def create_plan(
    data: CreatePlanRequest,
    current_user: dict = Depends(require_permission(PERMISSIONS.MANAGE_SUBSCRIPTIONS)),
):
    """Create a new subscription plan (requires manage_subscriptions permission)."""
    return await _controller.create_plan(data, current_user["sub"])


@router.put("/api/admin/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    data: UpdatePlanRequest,
    current_user: dict = Depends(require_permission(PERMISSIONS.MANAGE_SUBSCRIPTIONS)),
):
    """Update a subscription plan (requires manage_subscriptions permission)."""
    return await _controller.update_plan(plan_id, data)


@router.delete("/api/admin/plans/{plan_id}")
async def deactivate_plan(
    plan_id: str,
    current_user: dict = Depends(require_permission(PERMISSIONS.MANAGE_SUBSCRIPTIONS)),
):
    """Soft-delete a subscription plan (requires manage_subscriptions permission)."""
    return await _controller.deactivate_plan(plan_id)


# ── Public routes (no auth) ─────────────────────────────────────────────

@router.get("/api/plans")
async def list_active_plans():
    """List all active subscription plans (public — no authentication required)."""
    return await _controller.list_active_plans()


@router.get("/api/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get a single subscription plan by ID (public)."""
    return await _controller.get_plan(plan_id)
