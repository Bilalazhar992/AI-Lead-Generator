"""Business logic for subscription management (plan changes, history).

change_event is determined by three simple price-based rules:
  - Current status is "trialing"           → "activated"   (leaving free trial)
  - New plan price  > current plan price   → "upgraded"
  - New plan price  < current plan price   → "downgraded"
  - Same plan / same price                 → "renewed"     (billing cycle change or re-subscription)

Plan change procedure (matches SCHEMA_REFERENCE.md):
  Step 1  Archive the current subscription doc → subscription_history
  Step 2  Overwrite the active subscription with new plan fields + reset usage counters
  Step 2 only runs after Step 1 succeeds, so if Step 1 fails nothing changes.
  If Step 2 fails, an orphaned history record may exist — acceptable for MVP;
  production deployments should use a MongoDB replica set + Motor session transaction.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.queries.subscription_queries import SubscriptionQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.subscription_schemas import ChangePlanRequest


# ── Serializers ───────────────────────────────────────────────────────────────

def _serialize_subscription(s: dict) -> dict:
    return {
        "id": str(s["_id"]),
        "business_id": str(s["business_id"]),
        "plan_id": str(s["plan_id"]),
        "plan_slug": s["plan_slug"],
        "status": s["status"],
        "billing_cycle": s.get("billing_cycle"),
        "period_start": s["period_start"].isoformat() if s.get("period_start") else None,
        "period_end": s["period_end"].isoformat() if s.get("period_end") else None,
        "trial_ends_at": s["trial_ends_at"].isoformat() if s.get("trial_ends_at") else None,
        "leads_count": s.get("leads_count", 0),
        "ai_messages_count": s.get("ai_messages_count", 0),
        "conversations_count": s.get("conversations_count", 0),
        "leads_limit_reached": s.get("leads_limit_reached", False),
        "messages_limit_reached": s.get("messages_limit_reached", False),
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


# ── change_event helper ───────────────────────────────────────────────────────

def _determine_change_event(
    current_sub: dict,
    current_plan: dict,
    new_plan: dict,
) -> str:
    """
    Simple price-comparison rule.

    - status is "trialing" or "cancelled"  → "activated"
      (first paid activation OR re-subscription after cancellation)
    - new price > old price                → "upgraded"
    - new price < old price                → "downgraded"
    - same price                           → "renewed"  (cycle change or same-plan renewal)
    """
    if current_sub.get("status") in ("trialing", "cancelled"):
        return "activated"
    new_price = new_plan.get("price_monthly_pkr", 0)
    old_price = current_plan.get("price_monthly_pkr", 0)
    if new_price > old_price:
        return "upgraded"
    if new_price < old_price:
        return "downgraded"
    return "renewed"


# ── Service ───────────────────────────────────────────────────────────────────

class SubscriptionImplementation:

    async def get_subscription(self, biz: dict) -> dict:
        """
        Return the active subscription and full history for a business.
        Accessible to business_owner (implicit) and business_staff with MANAGE_BILLING.
        """
        try:
            business_id: ObjectId = biz["business_id"]

            active = await SubscriptionQueries.find_active_by_business(business_id)
            if not active:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.SUBSCRIPTION_NOT_FOUND
                )

            history = await SubscriptionQueries.find_history_by_business(business_id)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "subscription": _serialize_subscription(active),
                    "history": [_serialize_history(h) for h in history],
                },
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def cancel_subscription(self, biz: dict) -> dict:
        """
        Cancel the active subscription.
        Archives the current doc to subscription_history with change_event: "cancelled",
        then sets status: "cancelled" on the active subscription record.
        """
        try:
            business_id: ObjectId = biz["business_id"]
            business_slug: str = biz["business_slug"]

            current_sub = await SubscriptionQueries.find_active_by_business(business_id)
            if not current_sub:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.SUBSCRIPTION_NOT_FOUND
                )

            if current_sub.get("status") == "cancelled":
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.CONFLICT, None, MESSAGES.SUBSCRIPTION_ALREADY_CANCELLED
                )

            now = datetime.now(timezone.utc)

            # Archive current state
            await SubscriptionQueries.archive_subscription({
                "business_id": business_id,
                "business_slug": business_slug,
                "plan_id": current_sub["plan_id"],
                "plan_slug": current_sub["plan_slug"],
                "status": current_sub["status"],
                "billing_cycle": current_sub.get("billing_cycle"),
                "period_start": current_sub.get("period_start"),
                "period_end": current_sub.get("period_end"),
                "trial_ends_at": current_sub.get("trial_ends_at"),
                "payment_method": current_sub.get("payment_method"),
                "payment_reference": current_sub.get("payment_reference"),
                "change_event": "cancelled",
                "leads_count": current_sub.get("leads_count", 0),
                "ai_messages_count": current_sub.get("ai_messages_count", 0),
                "conversations_count": current_sub.get("conversations_count", 0),
                "leads_limit_reached": current_sub.get("leads_limit_reached", False),
                "messages_limit_reached": current_sub.get("messages_limit_reached", False),
                "archived_at": now,
                "created_at": current_sub.get("created_at"),
            })

            updated = await SubscriptionQueries.update_active_subscription(
                business_id, {"status": "cancelled"}
            )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"subscription": _serialize_subscription(updated)},
                MESSAGES.SUBSCRIPTION_CANCELLED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def change_plan(self, biz: dict, data: ChangePlanRequest) -> dict:
        """
        Change the active subscription to a different plan.

        Procedure (archive-first, matches schema spec):
          1. Fetch current active subscription.
          2. Fetch target plan — must exist and be active.
          3. Compute change_event from price comparison.
          4. Archive current subscription doc to subscription_history.
          5. Overwrite active subscription with new plan data + reset counters.
        """
        try:
            business_id: ObjectId = biz["business_id"]
            business_slug: str = biz["business_slug"]

            # ── Step 1: current subscription ─────────────────────────
            current_sub = await SubscriptionQueries.find_active_by_business(business_id)
            if not current_sub:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.SUBSCRIPTION_NOT_FOUND
                )

            # ── Step 2: target plan ───────────────────────────────────
            new_plan = await SubscriptionQueries.find_plan_by_id(ObjectId(data.plan_id))
            if not new_plan or not new_plan.get("is_active"):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PLAN_NOT_FOUND
                )

            # Fetch current plan for change_event calculation
            current_plan = await SubscriptionQueries.find_plan_by_id(current_sub["plan_id"])

            # ── Step 3: change_event ──────────────────────────────────
            change_event = _determine_change_event(current_sub, current_plan or {}, new_plan)

            now = datetime.now(timezone.utc)
            period_days = 365 if data.billing_cycle == "annual" else 30

            # ── Step 4: archive current subscription to history ───────
            archive_doc = {
                "business_id": business_id,
                "business_slug": business_slug,
                "plan_id": current_sub["plan_id"],
                "plan_slug": current_sub["plan_slug"],
                "status": current_sub["status"],
                "billing_cycle": current_sub.get("billing_cycle"),
                "period_start": current_sub.get("period_start"),
                "period_end": current_sub.get("period_end"),
                "trial_ends_at": current_sub.get("trial_ends_at"),
                "payment_method": current_sub.get("payment_method"),
                "payment_reference": current_sub.get("payment_reference"),
                "change_event": change_event,
                "leads_count": current_sub.get("leads_count", 0),
                "ai_messages_count": current_sub.get("ai_messages_count", 0),
                "conversations_count": current_sub.get("conversations_count", 0),
                "leads_limit_reached": current_sub.get("leads_limit_reached", False),
                "messages_limit_reached": current_sub.get("messages_limit_reached", False),
                "archived_at": now,
                "created_at": current_sub.get("created_at"),
            }
            await SubscriptionQueries.archive_subscription(archive_doc)

            # ── Step 5: overwrite active subscription ─────────────────
            new_fields = {
                "plan_id": new_plan["_id"],
                "plan_slug": new_plan["slug"],
                "status": "active",
                "billing_cycle": data.billing_cycle,
                "period_start": now,
                "period_end": now + timedelta(days=period_days),
                "trial_ends_at": None,
                "payment_method": current_sub.get("payment_method"),
                "payment_reference": current_sub.get("payment_reference"),
                # Reset usage counters for the new period
                "leads_count": 0,
                "ai_messages_count": 0,
                "conversations_count": 0,
                "leads_limit_reached": False,
                "messages_limit_reached": False,
            }
            updated = await SubscriptionQueries.update_active_subscription(business_id, new_fields)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "subscription": _serialize_subscription(updated),
                    "change_event": change_event,
                },
                MESSAGES.SUBSCRIPTION_CHANGED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
