from fastapi import Depends, HTTPException
from bson import ObjectId
from app.utils.auth_dependency import get_current_user
from app.utils.constants import CODE, ROLES
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries


async def get_business_context(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    FastAPI dependency that resolves the caller's business context.

    Supports both business_owner (via owner_user_id lookup) and
    business_staff (via user_details.business_id stored in the JWT).

    Returns dict with keys: business_id, business_slug, subscription, plan, current_user.
    """
    role = current_user.get("role")
    user_id = current_user.get("sub")

    if role == ROLES.BUSINESS_OWNER:
        business = await BusinessQueries.find_by_owner(ObjectId(user_id))
    elif role == ROLES.BUSINESS_STAFF:
        business_id_str = current_user.get("business_id")
        if not business_id_str:
            raise HTTPException(status_code=CODE.FORBIDDEN, detail="Staff account not linked to a business")
        business = await BusinessQueries.find_by_id(ObjectId(business_id_str))
    else:
        raise HTTPException(status_code=CODE.FORBIDDEN, detail="Access denied for your role")

    if not business:
        raise HTTPException(status_code=CODE.RECORD_NOT_FOUND, detail="Business profile not found. Complete onboarding first.")

    subscription = await SubscriptionQueries.find_active_by_business(business["_id"])
    plan = None
    if subscription:
        plan = await SubscriptionQueries.find_plan_by_id(subscription["plan_id"])

    return {
        "business_id": business["_id"],
        "business_slug": business["slug"],
        "subscription": subscription,
        "plan": plan,
        "current_user": current_user,
    }
