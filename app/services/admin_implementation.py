"""Platform admin CRM — read-only views for super_admin and platform_staff.

All methods require VIEW_ANALYTICS permission (enforced at the route layer).
They provide cross-tenant visibility into businesses, subscriptions, products,
and staff — data that business owners/staff cannot access across tenants.

Query strategy — avoid N+1:
  list_businesses: 2 queries total
    1. fetch all businesses
    2. batch-fetch all subscriptions via $in on business_ids, merge in Python

  get_business_staff: 2 queries total
    1. fetch user_details where business_id matches
    2. batch-fetch users by user_ids from step 1, merge in Python
"""


from bson import ObjectId
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries

from app.queries.product_queries import ProductQueries
from app.queries.user_queries import UserQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES


# ── Serializers ───────────────────────────────────────────────────────────────

def _serialize_subscription_summary(s: dict | None) -> dict | None:
    if not s:
        return None
    return {
        "id": str(s["_id"]),
        "plan_id": str(s["plan_id"]),
        "plan_slug": s["plan_slug"],
        "status": s["status"],
        "billing_cycle": s.get("billing_cycle"),
        "period_end": s["period_end"].isoformat() if s.get("period_end") else None,
        "trial_ends_at": s["trial_ends_at"].isoformat() if s.get("trial_ends_at") else None,
        "leads_count": s.get("leads_count", 0),
        "ai_messages_count": s.get("ai_messages_count", 0),
        "conversations_count": s.get("conversations_count", 0),
        "leads_limit_reached": s.get("leads_limit_reached", False),
        "messages_limit_reached": s.get("messages_limit_reached", False),
    }


def _serialize_subscription_full(s: dict | None) -> dict | None:
    if not s:
        return None
    return {
        **_serialize_subscription_summary(s),
        "period_start": s["period_start"].isoformat() if s.get("period_start") else None,
        "payment_method": s.get("payment_method"),
        "updated_at": s["updated_at"].isoformat() if s.get("updated_at") else None,
    }


def _serialize_history(h: dict) -> dict:
    return {
        "id": str(h["_id"]),
        "plan_id": str(h["plan_id"]),
        "plan_slug": h["plan_slug"],
        "status": h["status"],
        "billing_cycle": h.get("billing_cycle"),
        "period_start": h["period_start"].isoformat() if h.get("period_start") else None,
        "period_end": h["period_end"].isoformat() if h.get("period_end") else None,
        "change_event": h.get("change_event"),
        "leads_count": h.get("leads_count", 0),
        "ai_messages_count": h.get("ai_messages_count", 0),
        "conversations_count": h.get("conversations_count", 0),
        "archived_at": h["archived_at"].isoformat() if h.get("archived_at") else None,
    }


def _serialize_business(b: dict) -> dict:
    return {
        "id": str(b["_id"]),
        "slug": b["slug"],
        "business_name": b["business_name"],
        "business_type": b.get("business_type"),
        "industry": b.get("industry"),
        "business_size": b.get("business_size"),
        "website_url": b.get("website_url"),
        "contact_email": b["contact_email"],
        "contact_phone": b.get("contact_phone"),
        "logo_url": b.get("logo_url"),
        "timezone": b.get("timezone"),
        "status": b["status"],
        "owner_user_id": str(b["owner_user_id"]),
        "created_at": b["created_at"].isoformat() if b.get("created_at") else None,
    }


def _serialize_product(p: dict) -> dict:
    return {
        "id": str(p["_id"]),
        "slug": p["slug"],
        "name": p["name"],
        "description": p.get("description"),
        "website_url": p.get("website_url"),
        "status": p["status"],
        "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
    }


def _serialize_staff_member(user: dict, detail: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
        "invited_by": str(detail["invited_by"]) if detail.get("invited_by") else None,
        "joined_at": detail["created_at"].isoformat() if detail.get("created_at") else None,
    }


# ── Service ───────────────────────────────────────────────────────────────────

class AdminImplementation:
    """Read-only CRM views for platform admin roles."""

    async def list_businesses(self) -> dict:
        """
        Return all businesses with their active subscription summary.
        Uses 2 queries total (businesses + batch subscription fetch).
        """
        try:
            businesses = await BusinessQueries.find_all()
            if not businesses:
                ResponseService.status = CODE.OK
                return ResponseService.response_service(
                    STATUS.SUCCESS, {"businesses": [], "total": 0}, MESSAGES.SUCCESS
                )

            business_ids = [b["_id"] for b in businesses]
            subscriptions = await SubscriptionQueries.find_by_business_ids(business_ids)

            # Build O(1) lookup: business_id (str) → subscription
            sub_map = {str(s["business_id"]): s for s in subscriptions}

            result = [
                {
                    **_serialize_business(b),
                    "subscription": _serialize_subscription_summary(
                        sub_map.get(str(b["_id"]))
                    ),
                }
                for b in businesses
            ]

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"businesses": result, "total": len(result)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business(self, business_id: str) -> dict:
        """Return a single business with its full active subscription."""
        try:
            biz_oid = ObjectId(business_id)
            business = await BusinessQueries.find_by_id(biz_oid)
            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND
                )

            subscription = await SubscriptionQueries.find_active_by_business(biz_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    **_serialize_business(business),
                    "subscription": _serialize_subscription_full(subscription),
                },
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_subscription(self, business_id: str) -> dict:
        """Return the active subscription and full change history for a business."""
        try:
            biz_oid = ObjectId(business_id)

            if not await BusinessQueries.find_by_id(biz_oid):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND
                )

            active = await SubscriptionQueries.find_active_by_business(biz_oid)
            if not active:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.SUBSCRIPTION_NOT_FOUND
                )

            history = await SubscriptionQueries.find_history_by_business(biz_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "subscription": _serialize_subscription_full(active),
                    "history": [_serialize_history(h) for h in history],
                },
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_products(self, business_id: str) -> dict:
        """Return all products belonging to a business."""
        try:
            biz_oid = ObjectId(business_id)

            if not await BusinessQueries.find_by_id(biz_oid):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND
                )

            products = await ProductQueries.find_all_by_business(biz_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"products": [_serialize_product(p) for p in products], "total": len(products)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    

    async def update_business_status(self, business_id: str, status: str) -> dict:
        """
        Set a business's status (active | suspended | cancelled).
        Requires MANAGE_BUSINESSES permission (enforced at route layer).
        """
        try:
            biz_oid = ObjectId(business_id)
            business = await BusinessQueries.find_by_id(biz_oid)
            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND
                )

            updated = await BusinessQueries.update_business(biz_oid, {"status": status})
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                _serialize_business(updated),
                MESSAGES.BUSINESS_STATUS_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_staff(self, business_id: str) -> dict:
        """
        Return all staff members of a business.
        Uses 2 queries: user_details by business_id, then users batch-fetched by id.
        """
        try:
            biz_oid = ObjectId(business_id)

            if not await BusinessQueries.find_by_id(biz_oid):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND
                )

            # Query 1 — user_details docs for this business
            staff_details = await UserQueries.find_staff_details_by_business(biz_oid)
            if not staff_details:
                ResponseService.status = CODE.OK
                return ResponseService.response_service(
                    STATUS.SUCCESS, {"staff": [], "total": 0}, MESSAGES.SUCCESS
                )

            # Query 2 — batch-fetch the user docs
            user_ids = [d["user_id"] for d in staff_details]
            users = await UserQueries.find_users_by_ids(user_ids)
            user_map = {str(u["_id"]): u for u in users}

            # Merge
            staff = [
                _serialize_staff_member(user_map[str(d["user_id"])], d)
                for d in staff_details
                if str(d["user_id"]) in user_map
            ]

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"staff": staff, "total": len(staff)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
