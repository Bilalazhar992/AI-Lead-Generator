from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.config import settings
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries
from app.utils.slug_helper import generate_slug, make_unique_slug
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES, PERMISSIONS
from app.utils.messages import MESSAGES
from app.models.business_schemas import BusinessCreateRequest, BusinessUpdateRequest


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
        "onboarding_completed": b["onboarding_completed"],
        "created_at": b["created_at"].isoformat(),
    }


def _serialize_subscription(s: dict) -> dict:
    return {
        "id": str(s["_id"]),
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
    }


class BusinessImplementation:
    """Business logic for multi-business management."""

    async def create_business(self, data: BusinessCreateRequest, owner_user_id: str) -> dict:
        """
        Create a new business for the signed-in owner and seed a trial subscription.
        A business_owner may create multiple businesses — no one-per-owner restriction.
        """
        try:
            owner_id = ObjectId(owner_user_id)

            base_slug = generate_slug(data.business_name)
            slug = base_slug
            while await BusinessQueries.slug_exists(slug):
                slug = make_unique_slug(base_slug)

            plan = await SubscriptionQueries.find_plan_by_slug("free-trial")
            if not plan:
                ResponseService.status = CODE.INTERNAL_SERVER_ERROR
                return ResponseService.response_service(STATUS.EXCEPTION, None, MESSAGES.EXCEPTION)

            now = datetime.now(timezone.utc)
            trial_ends_at = now + timedelta(days=settings.TRIAL_PERIOD_DAYS)

            business = await BusinessQueries.create_business({
                "slug": slug,
                "business_name": data.business_name,
                "business_type": data.business_type,
                "industry": data.industry,
                "business_size": data.business_size,
                "website_url": data.website_url,
                "contact_email": data.contact_email,
                "contact_phone": data.contact_phone,
                "logo_url": None,
                "timezone": data.timezone,
                "owner_user_id": owner_id,
                "status": "active",
                "onboarding_completed": True,
                "created_at": now,
                "updated_at": now,
            })

            subscription = await SubscriptionQueries.create_subscription({
                "business_id": business["_id"],
                "business_slug": slug,
                "plan_id": plan["_id"],
                "plan_slug": plan["slug"],
                "status": "trialing",
                "billing_cycle": "monthly",
                "period_start": now,
                "period_end": trial_ends_at,
                "trial_ends_at": trial_ends_at,
                "payment_method": None,
                "payment_reference": None,
                "leads_count": 0,
                "ai_messages_count": 0,
                "conversations_count": 0,
                "leads_limit_reached": False,
                "messages_limit_reached": False,
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "business": _serialize_business(business),
                    "subscription": _serialize_subscription(subscription),
                },
                MESSAGES.BUSINESS_CREATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_my_businesses(self, owner_user_id: str) -> dict:
        """Return all businesses owned by the signed-in owner."""
        try:
            owner_id = ObjectId(owner_user_id)
            businesses = await BusinessQueries.find_all_by_owner(owner_id)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "businesses": [_serialize_business(b) for b in businesses],
                    "total": len(businesses),
                },
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_by_id(self, business_id: str, owner_user_id: str) -> dict:
        """
        Return a specific business that the signed-in owner owns.
        Returns 404 if the business does not exist or does not belong to this owner.
        """
        try:
            owner_id = ObjectId(owner_user_id)
            biz_oid = ObjectId(business_id)
            business = await BusinessQueries.find_by_owner_and_id(biz_oid, owner_id)

            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            subscription = await SubscriptionQueries.find_active_by_business(business["_id"])

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "business": _serialize_business(business),
                    "subscription": _serialize_subscription(subscription) if subscription else None,
                },
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_business(
        self, business_id: str, data: BusinessUpdateRequest, owner_user_id: str
    ) -> dict:
        """
        Update a specific business owned by the signed-in owner.
        The compound filter { _id, owner_user_id } prevents cross-owner mutation at the DB level.
        """
        try:
            owner_id = ObjectId(owner_user_id)
            biz_oid = ObjectId(business_id)

            business = await BusinessQueries.find_by_owner_and_id(biz_oid, owner_id)
            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(STATUS.BAD_REQUEST, None, MESSAGES.INVALID_PARAMETERS)

            updated = await BusinessQueries.update_by_owner(biz_oid, owner_id, update_data)
            if not updated:
                ResponseService.status = CODE.FORBIDDEN
                return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PERMISSION_DENIED)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS, _serialize_business(updated), MESSAGES.BUSINESS_UPDATED
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def delete_business(self, business_id: str, current_user: dict) -> dict:
        """
        Delete a business and its linked subscription.

        Access rules:
          - business_owner: can only delete a business they own (business_id must match owner).
          - super_admin: can delete any business by ID.
          - platform_staff with MANAGE_BUSINESSES: can delete any business by ID.
        """
        try:
            role = current_user.get("role")
            user_oid = ObjectId(current_user["sub"])
            biz_oid = ObjectId(business_id)

            if role == ROLES.PLATFORM_STAFF:
                if PERMISSIONS.MANAGE_BUSINESSES not in current_user.get("permissions", []):
                    ResponseService.status = CODE.FORBIDDEN
                    return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PERMISSION_DENIED)

            if role == ROLES.BUSINESS_OWNER:
                business = await BusinessQueries.find_by_owner_and_id(biz_oid, user_oid)
                if not business:
                    ResponseService.status = CODE.RECORD_NOT_FOUND
                    return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)
                deleted = await BusinessQueries.delete_by_owner(biz_oid, user_oid)
            else:
                business = await BusinessQueries.find_by_id(biz_oid)
                if not business:
                    ResponseService.status = CODE.RECORD_NOT_FOUND
                    return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)
                deleted = await BusinessQueries.delete_by_id(biz_oid)

            if not deleted:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            await SubscriptionQueries.delete_by_business(biz_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, None, MESSAGES.BUSINESS_DELETED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_staff_business(self, staff_user_id: str) -> dict:
        """Return the business a business_staff member belongs to via user_details.business_id."""
        try:
            from app.queries.user_queries import UserQueries
            staff_oid = ObjectId(staff_user_id)
            user_details = await UserQueries.find_user_details(staff_oid)

            if not user_details or not user_details.get("business_id"):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            business = await BusinessQueries.find_by_id(user_details["business_id"])
            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            subscription = await SubscriptionQueries.find_active_by_business(business["_id"])
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {
                    "business": _serialize_business(business),
                    "subscription": _serialize_subscription(subscription) if subscription else None,
                },
                MESSAGES.SUCCESS,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
