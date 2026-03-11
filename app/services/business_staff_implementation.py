"""Business logic for business staff invitation (business_owner only)."""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.user_queries import UserQueries
from app.utils.password_helper import hash_password
from app.queries.business_queries import BusinessQueries
from app.queries.subscription_queries import SubscriptionQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES
from app.utils.messages import MESSAGES
from app.models.staff_schemas import InviteBusinessStaffRequest


def _serialize_staff(user: dict) -> dict:
    """Convert a MongoDB user document to a JSON-safe dict."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
    }


class BusinessStaffImplementation:
    """Handles business staff invitation by business_owner."""

    async def invite(
        self, data: InviteBusinessStaffRequest, owner_user_id: str
    ) -> dict:
        """
        Create a new business_staff user linked to the owner's business.
        - Resolves business from the owner.
        - Checks team member limit from the subscription plan.
        - Validates email uniqueness.
        - Creates documents in both `users` and `user_details`.
        """
        try:
            owner_oid = ObjectId(owner_user_id)

            # ── Resolve the owner's business ─────────────────────────
            business = await BusinessQueries.find_by_owner(owner_oid)
            if not business:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.BUSINESS_REQUIRED
                )

            business_id = business["_id"]

            # ── Check team member limit ──────────────────────────────
            subscription = await SubscriptionQueries.find_active_by_business(business_id)
            if subscription:
                plan = await SubscriptionQueries.find_plan_by_id(subscription.get("plan_id"))
                if plan:
                    max_members = plan.get("max_team_members", 1)
                    current_count = await UserQueries.count_staff_by_business(business_id)
                    if current_count >= max_members:
                        ResponseService.status = CODE.FORBIDDEN
                        return ResponseService.response_service(
                            STATUS.FAILURE, None, MESSAGES.TEAM_LIMIT_REACHED
                        )

            # ── Check duplicate email ────────────────────────────────
            if await UserQueries.find_by_email(data.email):
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.DUPLICATE, None, MESSAGES.STAFF_EMAIL_EXISTS
                )

            now = datetime.now(timezone.utc)

            # ── Create user document ─────────────────────────────────
            user = await UserQueries.create_user({
                "email": data.email,
                "password_hash": hash_password(data.password),
                "first_name": data.first_name,
                "last_name": data.last_name,
                "role": ROLES.BUSINESS_STAFF,
                "permissions": data.permissions,
                "is_active": True,
                "last_login_at": None,
                "created_at": now,
                "updated_at": now,
            })

            # ── Create user_details document with business link ──────
            await UserQueries.create_user_details({
                "user_id": user["_id"],
                "phone": None,
                "avatar_url": None,
                "language": "en",
                "business_id": business_id,
                "business_slug": business.get("slug"),
                "invited_by": owner_oid,
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"user": _serialize_staff(user)},
                MESSAGES.STAFF_INVITED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
