from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.config import settings
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries
from app.queries.user_queries import UserQueries
from app.utils.slug_helper import generate_slug, make_unique_slug
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES, PERMISSIONS
from app.utils.messages import MESSAGES
from app.models.business_schemas import BusinessOnboardRequest, BusinessUpdateRequest


def _serialize_business(b: dict) -> dict:
    return {
        "id": str(b["_id"]),
        "slug": b["slug"],
        "business_name": b["business_name"],
        "business_type": b.get("business_type"),
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
    """Business logic for business onboarding and profile management."""

    async def onboard(self, data: BusinessOnboardRequest, owner_user_id: str) -> dict:
        try:
            owner_id = ObjectId(owner_user_id)

            # One business per owner
            if await BusinessQueries.find_by_owner(owner_id):
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(STATUS.CONFLICT, None, MESSAGES.BUSINESS_ALREADY_EXISTS)

            # Resolve unique slug — retry with suffix on collision (extremely rare)
            base_slug = generate_slug(data.business_name)
            slug = base_slug
            while await BusinessQueries.slug_exists(slug):
                slug = make_unique_slug(base_slug)

            # Trial plan must be seeded at startup
            plan = await SubscriptionQueries.find_plan_by_slug("free-trial")
            if not plan:
                ResponseService.status = CODE.INTERNAL_SERVER_ERROR
                return ResponseService.response_service(STATUS.EXCEPTION, None, MESSAGES.EXCEPTION)

            now = datetime.now(timezone.utc)
            trial_ends_at = now + timedelta(days=settings.TRIAL_PERIOD_DAYS)

            # Create business document
            business = await BusinessQueries.create_business({
                "slug": slug,
                "business_name": data.business_name,
                "business_type": data.business_type,
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

            # Seed trial subscription
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

            # Enrich owner's user_details with business profile info
            await UserQueries.update_user_details_by_user_id(owner_id, {
                "company_name": data.business_name,
                "company_website": data.company_website,
                "industry": data.industry,
                "business_size": data.business_size,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"business": _serialize_business(business), "subscription": _serialize_subscription(subscription)},
                MESSAGES.BUSINESS_CREATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_my_business(self, owner_user_id: str) -> dict:
        try:
            owner_id = ObjectId(owner_user_id)
            business = await BusinessQueries.find_by_owner(owner_id)

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

    async def get_all_businesses(self, current_user: dict) -> dict:
        try:
            # Platform staff must carry the MANAGE_BUSINESSES permission;
            # super_admin is granted implicit access.
            if current_user.get("role") == ROLES.PLATFORM_STAFF:
                if PERMISSIONS.MANAGE_BUSINESSES not in current_user.get("permissions", []):
                    ResponseService.status = CODE.FORBIDDEN
                    return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PERMISSION_DENIED)

            businesses = await BusinessQueries.find_all()
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"businesses": [_serialize_business(b) for b in businesses], "total": len(businesses)},
                MESSAGES.SUCCESS,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_staff_business(self, staff_user_id: str) -> dict:
        """Return the business a business_staff member belongs to via user_details.business_id."""
        try:
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

    async def update_my_business(self, data: BusinessUpdateRequest, owner_user_id: str) -> dict:
        try:
            owner_id = ObjectId(owner_user_id)
            business = await BusinessQueries.find_by_owner(owner_id)

            if not business:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.BUSINESS_NOT_FOUND)

            # Explicit ownership assertion — ensures the authenticated user is the owner
            # of this specific business document, not just any business_owner role holder.
            if business["owner_user_id"] != owner_id:
                ResponseService.status = CODE.FORBIDDEN
                return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PERMISSION_DENIED)

            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(STATUS.BAD_REQUEST, None, MESSAGES.INVALID_PARAMETERS)

            # compound-filter write: MongoDB only updates if _id AND owner_user_id both match
            updated = await BusinessQueries.update_by_owner(business["_id"], owner_id, update_data)
            if not updated:
                ResponseService.status = CODE.FORBIDDEN
                return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PERMISSION_DENIED)

            # Mirror name change into user_details.company_name
            if "business_name" in update_data:
                await UserQueries.update_user_details_by_user_id(owner_id, {
                    "company_name": update_data["business_name"],
                    "updated_at": datetime.now(timezone.utc),
                })

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, _serialize_business(updated), MESSAGES.BUSINESS_UPDATED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
