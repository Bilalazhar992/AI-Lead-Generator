"""Business logic for platform staff invitation (super_admin only)."""

from datetime import datetime, timezone
from app.queries.user_queries import UserQueries
from app.utils.password_helper import hash_password
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES
from app.utils.messages import MESSAGES
from app.models.staff_schemas import InvitePlatformStaffRequest


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


class PlatformStaffImplementation:
    """Handles platform staff invitation by super_admin."""

    async def invite(self, data: InvitePlatformStaffRequest) -> dict:
        """
        Create a new platform_staff user.
        - Validates email uniqueness.
        - Hashes the password.
        - Creates documents in both `users` and `user_details`.
        """
        try:
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
                "role": ROLES.PLATFORM_STAFF,
                "permissions": data.permissions,
                "is_active": True,
                "last_login_at": None,
                "created_at": now,
                "updated_at": now,
            })

            # ── Create user_details document ─────────────────────────
            await UserQueries.create_user_details({
                "user_id": user["_id"],
                "phone": None,
                "avatar_url": None,
                "language": "en",
                "department": data.department,
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
