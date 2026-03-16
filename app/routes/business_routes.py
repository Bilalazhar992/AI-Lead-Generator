"""Business management routes.

URL design:
  POST   /api/businesses                  → business_owner: create a new business
  GET    /api/businesses                  → business_owner: list all my businesses
  GET    /api/businesses/my-business      → business_staff: get the business they belong to
  GET    /api/businesses/{business_id}    → business_owner: get a specific business
  PUT    /api/businesses/{business_id}    → business_owner: update a specific business
  DELETE /api/businesses/{business_id}    → business_owner: delete own business
                                             super_admin / platform_staff: delete any business

Platform admin list/detail views live in admin_routes.py (/api/admin/businesses/...).

IMPORTANT: /my-business must be defined BEFORE /{business_id}
to avoid being swallowed by the path catch-all.

Security layers:
  Layer 1 — get_current_user(): validates JWT signature, type, and jti blacklist.
  Layer 2 — require_role(): rejects tokens with a disallowed role.
  Layer 3 — service layer: ownership assertion (owner_user_id match) or permission check.
  Layer 4 — DB write filter: compound { _id, owner_user_id } prevents cross-owner mutation.
"""

from fastapi import APIRouter, Depends
from app.controllers.business_controller import BusinessController
from app.models.business_schemas import BusinessCreateRequest, BusinessUpdateRequest
from app.utils.auth_dependency import require_role
from app.utils.constants import ROLES

router = APIRouter(prefix="/api/businesses", tags=["Business"])
_controller = BusinessController()


# ── Owner: create a new business ─────────────────────────────────────────────
@router.post("", status_code=201)
async def create_business(
    data: BusinessCreateRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Create a new business for the signed-in owner and seed a trial subscription."""
    return await _controller.create_business(data, current_user["sub"])


# ── Owner: list all my businesses ────────────────────────────────────────────
@router.get("")
async def get_my_businesses(
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """List all businesses owned by the signed-in owner."""
    return await _controller.get_my_businesses(current_user["sub"])


# ── Staff: get the business they belong to ───────────────────────────────────
# Must be defined BEFORE /{business_id} to avoid being swallowed by the catch-all.
@router.get("/my-business")
async def get_staff_business(
    current_user: dict = Depends(require_role(ROLES.BUSINESS_STAFF)),
):
    """Get the business the signed-in staff member belongs to."""
    return await _controller.get_staff_business(current_user["sub"])


# ── Owner: get a specific business ───────────────────────────────────────────
@router.get("/{business_id}")
async def get_business(
    business_id: str,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Get a specific business owned by the signed-in owner."""
    return await _controller.get_business_by_id(business_id, current_user["sub"])


# ── Owner: update a specific business ────────────────────────────────────────
@router.put("/{business_id}")
async def update_business(
    business_id: str,
    data: BusinessUpdateRequest,
    current_user: dict = Depends(require_role(ROLES.BUSINESS_OWNER)),
):
    """Update a specific business owned by the signed-in owner."""
    return await _controller.update_business(business_id, data, current_user["sub"])


# ── Owner / Admin: delete a business ─────────────────────────────────────────
@router.delete("/{business_id}", status_code=200)
async def delete_business(
    business_id: str,
    current_user: dict = Depends(
        require_role(ROLES.BUSINESS_OWNER, ROLES.SUPER_ADMIN, ROLES.PLATFORM_STAFF)
    ),
):
    """
    Delete a business and its linked subscription.
      - business_owner: must own the business.
      - super_admin: can delete any business.
      - platform_staff: requires MANAGE_BUSINESSES permission.
    """
    return await _controller.delete_business(business_id, current_user)
