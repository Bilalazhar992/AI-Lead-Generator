"""Business logic for platform staff management."""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.user_queries import UserQueries
from app.utils.password_helper import hash_password
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES
from app.utils.messages import MESSAGES
from app.models.staff_schemas import (
    InvitePlatformStaffRequest,
    UpdatePlatformStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)


def _serialize_staff(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
    }


class PlatformStaffImplementation:

    async def invite(self, data: InvitePlatformStaffRequest) -> dict:
        """Create a new platform_staff user."""
        try:
            if await UserQueries.find_by_email(data.email):
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.DUPLICATE, None, MESSAGES.STAFF_EMAIL_EXISTS
                )

            now = datetime.now(timezone.utc)
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
                STATUS.SUCCESS, {"user": _serialize_staff(user)}, MESSAGES.STAFF_INVITED
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def list_staff(self) -> dict:
        """Return all platform_staff users."""
        try:
            users = await UserQueries.find_all_by_role(ROLES.PLATFORM_STAFF)
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"staff": [_serialize_staff(u) for u in users], "total": len(users)},
                MESSAGES.SUCCESS,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_permissions(
        self, user_id: str, data: UpdatePlatformStaffPermissionsRequest
    ) -> dict:
        """Replace the permission set of a platform_staff user."""
        try:
            user_oid = ObjectId(user_id)
            user = await UserQueries.find_by_id(user_oid)
            if not user or user.get("role") != ROLES.PLATFORM_STAFF:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            updated = await UserQueries.update_user(user_oid, {"permissions": data.permissions})
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS, {"user": _serialize_staff(updated)}, MESSAGES.PERMISSIONS_UPDATED
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_status(self, user_id: str, data: UpdateStaffStatusRequest) -> dict:
        """Activate or deactivate a platform_staff account."""
        try:
            user_oid = ObjectId(user_id)
            user = await UserQueries.find_by_id(user_oid)
            if not user or user.get("role") != ROLES.PLATFORM_STAFF:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.STAFF_NOT_FOUND
                )

            updated = await UserQueries.update_user(user_oid, {"is_active": data.is_active})
            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS, {"user": _serialize_staff(updated)}, MESSAGES.STAFF_STATUS_UPDATED
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
