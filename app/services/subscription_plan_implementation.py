"""Business logic for subscription plan management.

Accessible to super_admin and platform_staff with MANAGE_SUBSCRIPTIONS permission.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.subscription_queries import SubscriptionQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.subscription_schemas import CreatePlanRequest, UpdatePlanRequest


def _serialize_plan(plan: dict) -> dict:
    """Convert a MongoDB subscription_plans document to a JSON-safe dict."""
    return {
        "id": str(plan["_id"]),
        "name": plan["name"],
        "slug": plan["slug"],
        "price_monthly_pkr": plan["price_monthly_pkr"],
        "price_annual_pkr": plan["price_annual_pkr"],
        "max_products": plan["max_products"],
        "max_leads_per_month": plan["max_leads_per_month"],
        "max_ai_messages_per_month": plan["max_ai_messages_per_month"],
        "max_team_members": plan["max_team_members"],
        "whatsapp_enabled": plan["whatsapp_enabled"],
        "widget_enabled": plan["widget_enabled"],
        "remove_branding": plan["remove_branding"],
        "is_active": plan["is_active"],
        "display_order": plan["display_order"],
        "created_by": str(plan["created_by"]) if plan.get("created_by") else None,
        "created_at": plan["created_at"].isoformat() if plan.get("created_at") else None,
    }


class SubscriptionPlanImplementation:
    """CRUD operations for the subscription plan catalog."""

    async def create_plan(self, data: CreatePlanRequest, created_by: str) -> dict:
        """Create a new subscription plan. Slug must be unique."""
        try:
            # ── Check slug uniqueness ────────────────────────────────
            existing = await SubscriptionQueries.find_plan_by_slug_any(data.slug)
            if existing:
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.DUPLICATE, None, MESSAGES.PLAN_SLUG_EXISTS
                )

            now = datetime.now(timezone.utc)
            plan = await SubscriptionQueries.create_plan({
                "name": data.name,
                "slug": data.slug,
                "price_monthly_pkr": data.price_monthly_pkr,
                "price_annual_pkr": data.price_annual_pkr,
                "max_products": data.max_products,
                "max_leads_per_month": data.max_leads_per_month,
                "max_ai_messages_per_month": data.max_ai_messages_per_month,
                "max_team_members": data.max_team_members,
                "whatsapp_enabled": data.whatsapp_enabled,
                "widget_enabled": data.widget_enabled,
                "remove_branding": data.remove_branding,
                "is_active": data.is_active,
                "display_order": data.display_order,
                "created_by": ObjectId(created_by),
                "created_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"plan": _serialize_plan(plan)},
                MESSAGES.PLAN_CREATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_active_plans(self) -> dict:
        """Return all active plans sorted by display_order. Public endpoint."""
        try:
            plans = await SubscriptionQueries.find_all_active_plans()

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"plans": [_serialize_plan(p) for p in plans]},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_plan(self, plan_id: str) -> dict:
        """Get a single plan by ID."""
        try:
            plan = await SubscriptionQueries.find_plan_by_id(ObjectId(plan_id))
            if not plan:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PLAN_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"plan": _serialize_plan(plan)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_plan(self, plan_id: str, data: UpdatePlanRequest) -> dict:
        """Partial update — only non-null fields are written."""
        try:
            plan_oid = ObjectId(plan_id)

            # ── Check plan exists ────────────────────────────────────
            existing = await SubscriptionQueries.find_plan_by_id(plan_oid)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PLAN_NOT_FOUND
                )

            # ── Build update dict (exclude None values) ──────────────
            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.INVALID_PARAMETERS
                )

            updated = await SubscriptionQueries.update_plan(plan_oid, update_data)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"plan": _serialize_plan(updated)},
                MESSAGES.PLAN_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def deactivate_plan(self, plan_id: str) -> dict:
        """Soft-delete a plan by setting is_active = False."""
        try:
            plan_oid = ObjectId(plan_id)

            success = await SubscriptionQueries.deactivate_plan(plan_oid)
            if not success:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PLAN_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS, None, MESSAGES.PLAN_DEACTIVATED
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
