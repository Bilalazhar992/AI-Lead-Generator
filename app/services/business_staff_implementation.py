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
from app.models.staff_schemas import (
    InviteBusinessStaffRequest,
    UpdateBusinessStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)


def _serialize_staff(user: dict, detail: dict | None = None) -> dict:
    base = {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
    }
    if detail:
        base["invited_by"] = str(detail["invited_by"]) if detail.get("invited_by") else None
        base["joined_at"] = detail["created_at"].isoformat() if detail.get("created_at") else None
    return base


class BusinessStaffImplementation:
    """Handles business staff invitation by a business_owner."""

    async def invite(
        self, data: InviteBusinessStaffRequest, owner_user_id: str, business_id: str
    ) -> dict:
        """
        Create a new business_staff user linked to a specific business.

        Steps:
          1. Verify the owner actually owns the given business_id.
          2. Check the team-member limit from that business's subscription plan.
          3. Validate email uniqueness.
          4. Create documents in `users` and `user_details`.
        """
        try:
            owner_oid = ObjectId(owner_user_id)
            biz_oid = ObjectId(business_id)

            # ── Verify the owner owns this specific business ──────────
            business = await BusinessQueries.find_by_owner_and_id(biz_oid, owner_oid)
            if not business:
                ResponseService.status = CODE.FORBIDDEN
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.PERMISSION_DENIED
                )

            # ── Check team member limit ───────────────────────────────
            subscription = await SubscriptionQueries.find_active_by_business(biz_oid)
            if subscription:
                plan = await SubscriptionQueries.find_plan_by_id(subscription.get("plan_id"))
                if plan:
                    max_members = plan.get("max_team_members", 1)
                    current_count = await UserQueries.count_staff_by_business(biz_oid)
                    if current_count >= max_members:
                        ResponseService.status = CODE.FORBIDDEN
                        return ResponseService.response_service(
                            STATUS.FAILURE, None, MESSAGES.TEAM_LIMIT_REACHED
                        )

            # ── Check duplicate email ─────────────────────────────────
            if await UserQueries.find_by_email(data.email):
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.DUPLICATE, None, MESSAGES.STAFF_EMAIL_EXISTS
                )

            now = datetime.now(timezone.utc)

            # ── Create user document ──────────────────────────────────
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

            # ── Create user_details document with business link ───────
            await UserQueries.create_user_details({
                "user_id": user["_id"],
                "phone": None,
                "avatar_url": None,
                "language": "en",
                "business_id": biz_oid,
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

    async def list_staff(self, biz: dict) -> dict:
        """
        Return all staff members for a business.
        Uses 2 queries: user_details by business_id, then users batch-fetched by id.
        Accessible to business_owner (implicit) and business_staff with MANAGE_TEAM.
        """
        try:
            business_id: ObjectId = biz["business_id"]

            # Query 1 — user_details for this business
            staff_details = await UserQueries.find_staff_details_by_business(business_id)
            if not staff_details:
                ResponseService.status = CODE.OK
                return ResponseService.response_service(
                    STATUS.SUCCESS, {"staff": [], "total": 0}, MESSAGES.SUCCESS
                )

            # Query 2 — batch-fetch the corresponding user docs
            user_ids = [d["user_id"] for d in staff_details]
            users = await UserQueries.find_users_by_ids(user_ids)
            user_map = {str(u["_id"]): u for u in users}

            staff = [
                _serialize_staff(user_map[str(d["user_id"])], d)
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
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_permissions(
        self,
        user_id: str,
        data: UpdateBusinessStaffPermissionsRequest,
        biz: dict,
    ) -> dict:
        """
        Replace a business_staff member's permissions.
        Verifies the staff member belongs to the calling user's business
        before writing, preventing cross-business permission changes.
        """
        try:
            user_oid = ObjectId(user_id)
            business_id: ObjectId = biz["business_id"]

            # Confirm the target user is actually a staff member of THIS business
            detail = await UserQueries.find_user_details(user_oid)
            if not detail or detail.get("business_id") != business_id:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            updated = await UserQueries.update_user(user_oid, {"permissions": data.permissions})
            if not updated:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"user": _serialize_staff(updated)},
                MESSAGES.PERMISSIONS_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_status(
        self,
        user_id: str,
        data: UpdateStaffStatusRequest,
        biz: dict,
    ) -> dict:
        """
        Activate or deactivate a business_staff account.
        Verifies the staff member belongs to the calling user's business.
        """
        try:
            user_oid = ObjectId(user_id)
            business_id: ObjectId = biz["business_id"]

            detail = await UserQueries.find_user_details(user_oid)
            if not detail or detail.get("business_id") != business_id:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            updated = await UserQueries.update_user(user_oid, {"is_active": data.is_active})
            if not updated:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"user": _serialize_staff(updated)},
                MESSAGES.STAFF_STATUS_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
