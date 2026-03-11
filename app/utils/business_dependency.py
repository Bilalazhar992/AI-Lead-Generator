"""FastAPI dependencies for resolving business context.

Used by all business-scoped routes. Supports both:
  - business_owner  → resolves business from `businesses.owner_user_id`
  - business_staff  → resolves business from `user_details.business_id`

Two public dependencies:
  get_business_context          — any business role (owner or staff) can call
  require_business_permission   — same + checks a specific permission
"""

from fastapi import Depends, HTTPException
from bson import ObjectId
from app.utils.auth_dependency import get_current_user
from app.utils.constants import CODE, ROLES
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries
from app.queries.user_queries import UserQueries


async def get_business_context(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Resolve the calling user's business context regardless of role.

    - business_owner  → lookup via businesses.owner_user_id
    - business_staff  → lookup via user_details.business_id

    Returns a dict with:
        - user_id       (str)
        - role          (str)
        - permissions   (list[str])
        - business_id   (ObjectId)
        - business_slug (str)
        - subscription  (dict | None)

    Raises 403 if the role is not business_owner / business_staff.
    Raises 400 if business cannot be resolved.
    """
    role = current_user.get("role")
    user_oid = ObjectId(current_user["sub"])

    # ── Resolve business_id based on role ────────────────────────────
    if role == ROLES.BUSINESS_OWNER:
        business = await BusinessQueries.find_by_owner(user_oid)
        if not business:
            raise HTTPException(
                status_code=CODE.BAD_REQUEST,
                detail="You must complete business onboarding first",
            )

    elif role == ROLES.BUSINESS_STAFF:
        details = await UserQueries.find_user_details(user_oid)
        if not details or not details.get("business_id"):
            raise HTTPException(
                status_code=CODE.BAD_REQUEST,
                detail="Your account is not linked to a business",
            )
        business = await BusinessQueries.find_by_id(details["business_id"])
        if not business:
            raise HTTPException(
                status_code=CODE.BAD_REQUEST,
                detail="The business linked to your account no longer exists",
            )

    else:
        raise HTTPException(
            status_code=CODE.FORBIDDEN,
            detail="Access denied — only business members can access this resource",
        )

    subscription = await SubscriptionQueries.find_active_by_business(business["_id"])

    return {
        "user_id": current_user["sub"],
        "role": role,
        "permissions": current_user.get("permissions", []),
        "business_id": business["_id"],
        "business_slug": business.get("slug"),
        "subscription": subscription,
    }


def require_business_permission(permission: str):
    """
    FastAPI dependency factory that enforces a business-level permission.

    business_owner always passes (they have all business permissions by default).
    business_staff must have the specific permission in their permissions list.

    Usage:
        biz = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS))
    """
    async def _check(
        biz: dict = Depends(get_business_context),
    ) -> dict:
        if biz["role"] == ROLES.BUSINESS_OWNER:
            return biz  # owner has all business permissions implicitly

        if permission not in biz.get("permissions", []):
            raise HTTPException(
                status_code=CODE.FORBIDDEN,
                detail=f"You need '{permission}' permission to perform this action",
            )
        return biz

    return _check
